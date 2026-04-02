from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from src.core.database import get_db
from src.domain.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Аналитика"])


class CompareBatchesRequest(BaseModel):
    batch_ids: list[int]


def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


@router.get("/dashboard")
async def get_dashboard(service: AnalyticsService = Depends(get_analytics_service)):
    """Статистика дашборда — из Redis кэша."""
    return await service.get_dashboard_stats()


@router.get("/batches/{batch_id}")
async def get_batch_stats(
    batch_id: int,
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Детальная статистика по партии."""
    stats = await service.get_batch_statistics(batch_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Batch not found")
    return stats


@router.post("/compare-batches")
async def compare_batches(
    data: CompareBatchesRequest,
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Сравнить несколько партий."""
    return await service.compare_batches(data.batch_ids)
