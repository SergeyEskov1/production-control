from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from typing import Optional

from src.data.models.product import Product


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, product: Product) -> Product:
        """Создать продукт"""
        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def get_by_code(self, unique_code: str) -> Optional[Product]:
        """Найти продукт по уникальному коду"""
        result = await self.db.execute(
            select(Product).where(Product.unique_code == unique_code)
        )
        return result.scalar_one_or_none()

    async def get_by_batch_id(self, batch_id: int) -> list[Product]:
        """Получить всю продукцию партии"""
        result = await self.db.execute(
            select(Product).where(Product.batch_id == batch_id)
        )
        return result.scalars().all()

    async def aggregate(self, product: Product) -> Product:
        """Отметить продукт как агрегированный"""
        product.is_aggregated = True
        product.aggregated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(product)
        return product
