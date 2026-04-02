from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from typing import Optional

from src.data.models.webhook import WebhookSubscription, WebhookDelivery


class WebhookRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_subscription(self, subscription: WebhookSubscription) -> WebhookSubscription:
        """Создать подписку."""
        self.db.add(subscription)
        await self.db.flush()
        await self.db.refresh(subscription)
        return subscription

    async def get_subscription(self, subscription_id: int) -> Optional[WebhookSubscription]:
        """Получить подписку по ID."""
        result = await self.db.execute(
            select(WebhookSubscription).where(WebhookSubscription.id == subscription_id)
        )
        return result.scalar_one_or_none()

    async def get_all_subscriptions(self) -> list[WebhookSubscription]:
        """Получить все подписки."""
        result = await self.db.execute(select(WebhookSubscription))
        return result.scalars().all()

    async def get_active_subscriptions_for_event(
        self, event: str
    ) -> list[WebhookSubscription]:
        """Получить активные подписки для конкретного события.
        Используется при отправке webhook — находим кому слать."""
        result = await self.db.execute(
            select(WebhookSubscription).where(
                WebhookSubscription.is_active == True,
            )
        )
        subscriptions = result.scalars().all()
        # Фильтруем по событию — JSON поле events содержит список
        return [s for s in subscriptions if event in s.events]

    async def update_subscription(self, subscription: WebhookSubscription) -> WebhookSubscription:
        """Обновить подписку."""
        await self.db.flush()
        await self.db.refresh(subscription)
        return subscription

    async def delete_subscription(self, subscription: WebhookSubscription):
        """Удалить подписку."""
        await self.db.delete(subscription)
        await self.db.flush()

    async def create_delivery(self, delivery: WebhookDelivery) -> WebhookDelivery:
        """Создать запись о доставке."""
        self.db.add(delivery)
        await self.db.flush()
        await self.db.refresh(delivery)
        return delivery

    async def get_deliveries(self, subscription_id: int) -> list[WebhookDelivery]:
        """Получить историю доставок для подписки."""
        result = await self.db.execute(
            select(WebhookDelivery)
            .where(WebhookDelivery.subscription_id == subscription_id)
            .order_by(WebhookDelivery.created_at.desc())
            .limit(50)
        )
        return result.scalars().all()
