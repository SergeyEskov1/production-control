from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.data.models.batch import Batch
from src.data.models.product import Product
from src.core.cache import get_cache, set_cache


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_stats(self) -> dict:
        cached = await get_cache("dashboard_stats")
        if cached:
            return cached

        total_batches = await self.db.scalar(select(func.count(Batch.id)))
        active_batches = await self.db.scalar(
            select(func.count(Batch.id)).where(Batch.is_closed == False)
        )
        total_products = await self.db.scalar(select(func.count(Product.id)))
        aggregated_products = await self.db.scalar(
            select(func.count(Product.id)).where(Product.is_aggregated == True)
        )

        stats = {
            "total_batches": total_batches or 0,
            "active_batches": active_batches or 0,
            "closed_batches": (total_batches or 0) - (active_batches or 0),
            "total_products": total_products or 0,
            "aggregated_products": aggregated_products or 0,
            "aggregation_rate": round(
                (aggregated_products or 0) / (total_products or 1) * 100, 2
            ),
        }

        await set_cache("dashboard_stats", stats, ttl=300)
        return stats

    async def get_batch_statistics(self, batch_id: int) -> dict:
        from src.data.repositories.batch_repository import BatchRepository
        repo = BatchRepository(self.db)
        batch = await repo.get_by_id(batch_id)
        if not batch:
            return None

        total = len(batch.products)
        aggregated = sum(1 for p in batch.products if p.is_aggregated)
        remaining = total - aggregated
        rate = round(aggregated / total * 100, 2) if total > 0 else 0

        return {
            "batch_info": {
                "id": batch.id,
                "batch_number": batch.batch_number,
                "batch_date": str(batch.batch_date),
                "is_closed": batch.is_closed,
            },
            "production_stats": {
                "total_products": total,
                "aggregated": aggregated,
                "remaining": remaining,
                "aggregation_rate": rate,
            },
        }

    async def compare_batches(self, batch_ids: list[int]) -> dict:
        from src.data.repositories.batch_repository import BatchRepository
        repo = BatchRepository(self.db)

        comparison = []
        for batch_id in batch_ids:
            batch = await repo.get_by_id(batch_id)
            if not batch:
                continue

            total = len(batch.products)
            aggregated = sum(1 for p in batch.products if p.is_aggregated)
            rate = round(aggregated / total * 100, 2) if total > 0 else 0

            comparison.append({
                "batch_id": batch.id,
                "batch_number": batch.batch_number,
                "total_products": total,
                "aggregated": aggregated,
                "rate": rate,
            })

        avg_rate = round(
            sum(c["rate"] for c in comparison) / len(comparison), 2
        ) if comparison else 0

        return {
            "comparison": comparison,
            "average": {"aggregation_rate": avg_rate},
        }
