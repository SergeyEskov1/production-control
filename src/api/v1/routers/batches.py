from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Optional

from src.core.database import get_db
from src.api.v1.schemas.batch import BatchCreate, BatchUpdate, BatchResponse, BatchListResponse
from src.data.repositories.batch_repository import BatchRepository
from src.domain.services.batch_service import BatchService

# Создаём роутер — группирует все эндпоинты для партий
router = APIRouter(prefix="/batches", tags=["Партии"])


def get_batch_service(db: AsyncSession = Depends(get_db)) -> BatchService:
    """Dependency injection — создаём сервис с репозиторием для каждого запроса"""
    repo = BatchRepository(db)
    return BatchService(repo)


@router.post("", status_code=201, response_model=list[BatchResponse])
async def create_batches(
    batches: list[BatchCreate],
    service: BatchService = Depends(get_batch_service),
):
    """Создание сменных заданий из 1С.
    Принимает список партий с русскими полями."""
    try:
        return await service.create_batches(batches)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=BatchListResponse)
async def get_batches(
    is_closed: Optional[bool] = Query(None, description="Фильтр по статусу"),
    batch_number: Optional[int] = Query(None, description="Номер партии"),
    batch_date: Optional[date] = Query(None, description="Дата партии"),
    work_center_id: Optional[int] = Query(None, description="ID рабочего центра"),
    shift: Optional[str] = Query(None, description="Смена"),
    offset: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(20, ge=1, le=100, description="Количество записей"),
    service: BatchService = Depends(get_batch_service),
):
    """Список партий с фильтрацией и пагинацией"""
    batches, total = await service.get_batches(
        is_closed=is_closed,
        batch_number=batch_number,
        batch_date=batch_date,
        work_center_id=work_center_id,
        shift=shift,
        offset=offset,
        limit=limit,
    )
    return BatchListResponse(
        items=batches,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: int,
    service: BatchService = Depends(get_batch_service),
):
    """Получить партию по ID со всей продукцией"""
    batch = await service.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@router.patch("/{batch_id}", response_model=BatchResponse)
async def update_batch(
    batch_id: int,
    data: BatchUpdate,
    service: BatchService = Depends(get_batch_service),
):
    """Обновить партию. При закрытии автоматически ставится closed_at."""
    batch = await service.update_batch(batch_id, data)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch
