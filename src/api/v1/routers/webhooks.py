from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.api.v1.schemas.webhook import WebhookCreate, WebhookUpdate, WebhookResponse, WebhookDeliveryResponse
from src.data.repositories.webhook_repository import WebhookRepository
from src.domain.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def get_webhook_service(db: AsyncSession = Depends(get_db)) -> WebhookService:
    return WebhookService(WebhookRepository(db))


@router.post("", status_code=201, response_model=WebhookResponse)
async def create_webhook(
    data: WebhookCreate,
    service: WebhookService = Depends(get_webhook_service),
):
    return await service.create_subscription(data)


@router.get("", response_model=list[WebhookResponse])
async def get_webhooks(service: WebhookService = Depends(get_webhook_service)):
    return await service.get_all()


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    data: WebhookUpdate,
    service: WebhookService = Depends(get_webhook_service),
):
    webhook = await service.update(webhook_id, data)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(
    webhook_id: int,
    service: WebhookService = Depends(get_webhook_service),
):
    deleted = await service.delete(webhook_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")


@router.get("/{webhook_id}/deliveries", response_model=list[WebhookDeliveryResponse])
async def get_deliveries(
    webhook_id: int,
    service: WebhookService = Depends(get_webhook_service),
):
    return await service.get_deliveries(webhook_id)
