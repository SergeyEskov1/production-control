from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import date

from src.data.models.batch import Batch
from src.data.models.work_center import WorkCenter


class BatchRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, batch: Batch) -> Batch:
        self.db.add(batch)
        await self.db.flush()
        await self.db.refresh(batch)
        return batch

    async def get_by_id(self, batch_id: int) -> Optional[Batch]:
        result = await self.db.execute(
            select(Batch)
            .options(selectinload(Batch.products))
            .where(Batch.id == batch_id)
        )
        return result.scalar_one_or_none()

    async def get_list(self, is_closed=None, batch_number=None, batch_date=None,
                       work_center_id=None, shift=None, offset=0, limit=20):
        query = select(Batch).options(selectinload(Batch.products))
        count_query = select(func.count(Batch.id))

        if is_closed is not None:
            query = query.where(Batch.is_closed == is_closed)
            count_query = count_query.where(Batch.is_closed == is_closed)
        if batch_number is not None:
            query = query.where(Batch.batch_number == batch_number)
            count_query = count_query.where(Batch.batch_number == batch_number)
        if batch_date is not None:
            query = query.where(Batch.batch_date == batch_date)
            count_query = count_query.where(Batch.batch_date == batch_date)
        if work_center_id is not None:
            query = query.where(Batch.work_center_id == work_center_id)
            count_query = count_query.where(Batch.work_center_id == work_center_id)
        if shift is not None:
            query = query.where(Batch.shift == shift)
            count_query = count_query.where(Batch.shift == shift)

        total = await self.db.scalar(count_query)
        result = await self.db.execute(query.offset(offset).limit(limit))
        return result.scalars().all(), total

    async def update(self, batch: Batch) -> Batch:
        await self.db.flush()
        await self.db.refresh(batch)
        return batch

    async def get_work_center_by_identifier(self, identifier: str) -> Optional[WorkCenter]:
        result = await self.db.execute(
            select(WorkCenter).where(WorkCenter.identifier == identifier)
        )
        return result.scalar_one_or_none()

    async def create_work_center(self, work_center: WorkCenter) -> WorkCenter:
        self.db.add(work_center)
        await self.db.flush()
        await self.db.refresh(work_center)
        return work_center
