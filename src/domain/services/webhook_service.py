from datetime import datetime, timezone
from typing import Optional

from src.data.models.webhook import WebhookSubscription
from src.data.repositories.webhook_repository import WebhookRepository
from src.api.v1.schemas.webhook import WebhookCreate, WebhookUpdate


class WebhookService:
    def __init__(self, repository: WebhookRepository):
        self.repository = repository

    async def create_subscription(self, data: WebhookCreate) -> WebhookSubscription:
        subscription = WebhookSubscription(
            url=data.url,
            events=data.events,
            secret_key=data.secret_key,
            retry_count=data.retry_count,
            timeout=data.timeout,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        return await self.repository.create_subscription(subscription)

    async def get_all(self) -> list[WebhookSubscription]:
        return await self.repository.get_all_subscriptions()

    async def get_by_id(self, subscription_id: int) -> Optional[WebhookSubscription]:
        return await self.repository.get_subscription(subscription_id)

    async def update(self, subscription_id: int, data: WebhookUpdate) -> Optional[WebhookSubscription]:
        subscription = await self.repository.get_subscription(subscription_id)
        if not subscription:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(subscription, field, value)

        subscription.updated_at = datetime.now(timezone.utc)
        return await self.repository.update_subscription(subscription)

    async def delete(self, subscription_id: int) -> bool:
        subscription = await self.repository.get_subscription(subscription_id)
        if not subscription:
            return False
        await self.repository.delete_subscription(subscription)
        return True

    async def get_deliveries(self, subscription_id: int):
        return await self.repository.get_deliveries(subscription_id)
