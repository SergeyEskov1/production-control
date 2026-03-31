import json
from datetime import datetime, timezone, date
from typing import Optional

from src.data.models.batch import Batch
from src.data.models.work_center import WorkCenter
from src.data.repositories.batch_repository import BatchRepository
from src.api.v1.schemas.batch import BatchCreate, BatchUpdate
from src.core.cache import get_cache, set_cache, delete_cache, delete_pattern


def _batch_to_dict(batch: Batch) -> dict:
    """Конвертируем SQLAlchemy объект в словарь для кэша.
    JSON не умеет сериализовать datetime и date — конвертируем в строки."""
    return {
        "id": batch.id,
        "is_closed": batch.is_closed,
        "closed_at": batch.closed_at.isoformat() if batch.closed_at else None,
        "task_description": batch.task_description,
        "shift": batch.shift,
        "team": batch.team,
        "batch_number": batch.batch_number,
        "batch_date": batch.batch_date.isoformat() if batch.batch_date else None,
        "nomenclature": batch.nomenclature,
        "ekn_code": batch.ekn_code,
        "shift_start": batch.shift_start.isoformat() if batch.shift_start else None,
        "shift_end": batch.shift_end.isoformat() if batch.shift_end else None,
        "created_at": batch.created_at.isoformat() if batch.created_at else None,
        "products": [
            {
                "id": p.id,
                "unique_code": p.unique_code,
                "batch_id": p.batch_id,
                "is_aggregated": p.is_aggregated,
                "aggregated_at": p.aggregated_at.isoformat() if p.aggregated_at else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in (batch.products or [])
        ],
    }


class BatchService:
    def __init__(self, repository: BatchRepository):
        self.repository = repository

    async def create_batches(self, batches_data: list[BatchCreate]) -> list[Batch]:
        """Создать партии и инвалидировать кэш списка."""
        created = []
        for data in batches_data:
            work_center = await self.repository.get_work_center_by_identifier(
                data.work_center_identifier
            )
            if not work_center:
                work_center = WorkCenter(
                    identifier=data.work_center_identifier,
                    name=data.work_center_name,
                )
                work_center = await self.repository.create_work_center(work_center)

            batch = Batch(
                is_closed=data.is_closed,
                task_description=data.task_description,
                work_center_id=work_center.id,
                shift=data.shift,
                team=data.team,
                batch_number=data.batch_number,
                batch_date=data.batch_date,
                nomenclature=data.nomenclature,
                ekn_code=data.ekn_code,
                shift_start=data.shift_start,
                shift_end=data.shift_end,
            )
            if data.is_closed:
                batch.closed_at = datetime.now(timezone.utc)

            batch = await self.repository.create(batch)
            created.append(batch)

        # Инвалидируем кэш списка партий — данные изменились
        # Удаляем ВСЕ варианты списка (с разными фильтрами)
        await delete_pattern("batches_list:*")

        return created

    async def get_batch(self, batch_id: int) -> Optional[Batch]:
        """Получить партию — сначала проверяем кэш, потом БД."""
        
        # Ключ кэша включает batch_id — у каждой партии свой ключ
        cache_key = f"batch_detail:{batch_id}"
        
        # Шаг 1 — смотрим в кэш
        cached = await get_cache(cache_key)
        if cached:
            # Данные есть в кэше — возвращаем без запроса к БД
            # Это быстро — Redis отвечает за ~1мс vs ~10мс для PostgreSQL
            return cached  # возвращаем словарь, роутер сам сериализует

        # Шаг 2 — кэш пуст, идём в БД
        batch = await self.repository.get_by_id(batch_id)
        if not batch:
            return None

        # Шаг 3 — сохраняем в кэш на 10 минут
        # Следующие запросы получат данные из Redis
        await set_cache(cache_key, _batch_to_dict(batch), ttl=600)

        return batch

    async def get_batches(self, **filters) -> tuple[list, int]:
        """Получить список с кэшированием.
        Ключ включает все фильтры — разные фильтры = разные ключи."""
        
        # Создаём уникальный ключ из всех фильтров
        # json.dumps с sort_keys гарантирует одинаковый порядок ключей
        filter_str = json.dumps(filters, sort_keys=True, default=str)
        cache_key = f"batches_list:{filter_str}"

        cached = await get_cache(cache_key)
        if cached:
            return cached["items"], cached["total"]

        batches, total = await self.repository.get_list(**filters)

        # Кэшируем на 1 минуту — список меняется чаще чем детали
        await set_cache(
            cache_key,
            {
                "items": [_batch_to_dict(b) for b in batches],
                "total": total,
            },
            ttl=60,
        )

        return batches, total

    async def update_batch(self, batch_id: int, data: BatchUpdate) -> Optional[Batch]:
        """Обновить партию и инвалидировать кэш."""
        batch = await self.repository.get_by_id(batch_id)
        if not batch:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(batch, field, value)

        if "is_closed" in update_data:
            if update_data["is_closed"]:
                batch.closed_at = datetime.now(timezone.utc)
            else:
                batch.closed_at = None

        batch = await self.repository.update(batch)

        # Инвалидируем кэш этой партии и список
        await delete_cache(f"batch_detail:{batch_id}")
        await delete_pattern("batches_list:*")

        return batch
