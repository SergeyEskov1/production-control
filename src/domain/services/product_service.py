from datetime import datetime, timezone
from typing import Optional

from src.data.models.product import Product
from src.data.repositories.product_repository import ProductRepository
from src.data.repositories.batch_repository import BatchRepository
from src.api.v1.schemas.product import ProductCreate


class ProductService:
    def __init__(self, product_repo: ProductRepository, batch_repo: BatchRepository):
        self.product_repo = product_repo
        self.batch_repo = batch_repo

    async def create_product(self, data: ProductCreate) -> Product:
        batch = await self.batch_repo.get_by_id(data.batch_id)
        if not batch:
            raise ValueError(f"Batch {data.batch_id} not found")
        if batch.is_closed:
            raise ValueError(f"Batch {data.batch_id} is closed")

        product = Product(
            unique_code=data.unique_code,
            batch_id=data.batch_id,
            created_at=datetime.now(timezone.utc),
        )
        return await self.product_repo.create(product)

    async def aggregate_products(self, batch_id: int, unique_codes: list[str]) -> dict:
        batch = await self.batch_repo.get_by_id(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")

        aggregated = 0
        errors = []

        for code in unique_codes:
            product = await self.product_repo.get_by_code(code)
            if not product:
                errors.append({"code": code, "reason": "not found"})
                continue
            if product.batch_id != batch_id:
                errors.append({"code": code, "reason": "belongs to different batch"})
                continue
            if product.is_aggregated:
                errors.append({"code": code, "reason": "already aggregated"})
                continue
            await self.product_repo.aggregate(product)
            aggregated += 1

        return {"total": len(unique_codes), "aggregated": aggregated,
                "failed": len(errors), "errors": errors}
