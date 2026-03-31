from datetime import datetime, timezone
from typing import Optional

from src.data.models.batch import Batch
from src.data.models.work_center import WorkCenter
from src.data.repositories.batch_repository import BatchRepository
from src.api.v1.schemas.batch import BatchCreate, BatchUpdate


class BatchService:
    """Сервисный слой — бизнес логика для партий.
    Не знает про HTTP, только про бизнес правила."""

    def __init__(self, repository: BatchRepository):
        self.repository = repository

    async def create_batches(self, batches_data: list[BatchCreate]) -> list[Batch]:
        """Создать несколько партий за один запрос (как требует 1С)"""
        created = []
        for data in batches_data:
            # Ищем рабочий центр по идентификатору
            work_center = await self.repository.get_work_center_by_identifier(
                data.work_center_identifier
            )
            # Если не существует — создаём автоматически
            if not work_center:
                work_center = WorkCenter(
                    identifier=data.work_center_identifier,
                    name=data.work_center_name,
                )
                work_center = await self.repository.create_work_center(work_center)

            # Создаём объект партии
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
            # Если партия создаётся уже закрытой — ставим время закрытия
            if data.is_closed:
                batch.closed_at = datetime.now(timezone.utc)

            batch = await self.repository.create(batch)
            created.append(batch)

        return created

    async def get_batch(self, batch_id: int) -> Optional[Batch]:
        """Получить партию по ID"""
        return await self.repository.get_by_id(batch_id)

    async def get_batches(self, **filters) -> tuple[list[Batch], int]:
        """Получить список партий с фильтрами"""
        return await self.repository.get_list(**filters)

    async def update_batch(
        self, batch_id: int, data: BatchUpdate
    ) -> Optional[Batch]:
        """Обновить партию.
        Бизнес правило: если is_closed меняется на True — ставим closed_at,
        если на False — убираем closed_at"""
        batch = await self.repository.get_by_id(batch_id)
        if not batch:
            return None

        # Применяем только переданные поля (partial update)
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(batch, field, value)

        # Бизнес правило для закрытия партии
        if "is_closed" in update_data:
            if update_data["is_closed"]:
                batch.closed_at = datetime.now(timezone.utc)
            else:
                batch.closed_at = None

        return await self.repository.update(batch)
