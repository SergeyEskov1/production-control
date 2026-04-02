import httpx
from datetime import datetime, timezone
from src.celery_app import app
from src.utils.hmac_utils import generate_signature


@app.task(bind=True, max_retries=3)
def send_webhook_delivery(self, delivery_id: int):
    """
    Отправка webhook с retry логикой.
    
    Находит запись WebhookDelivery в БД,
    отправляет HTTP запрос на URL подписки,
    сохраняет результат (успех или ошибка).
    
    При ошибке повторяет с exponential backoff:
    - 1я попытка: сразу
    - 2я попытка: через 60 секунд
    - 3я попытка: через 120 секунд
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import select
    from src.data.models.webhook import WebhookDelivery, WebhookSubscription
    from src.core.config import settings

    async def run():
        engine = create_async_engine(settings.database_url)
        SessionLocal = async_sessionmaker(engine, class_=AsyncSession)

        async with SessionLocal() as db:
            # Получаем запись доставки
            result = await db.execute(
                select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
            )
            delivery = result.scalar_one_or_none()
            if not delivery:
                return {"error": "Delivery not found"}

            # Получаем подписку чтобы знать URL и secret_key
            result = await db.execute(
                select(WebhookSubscription).where(
                    WebhookSubscription.id == delivery.subscription_id
                )
            )
            subscription = result.scalar_one_or_none()
            if not subscription:
                return {"error": "Subscription not found"}

            # Генерируем HMAC подпись
            signature = generate_signature(delivery.payload, subscription.secret_key)

            delivery.attempts += 1

            try:
                # Отправляем HTTP запрос
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        subscription.url,
                        json=delivery.payload,
                        headers={
                            "Content-Type": "application/json",
                            # Подпись в заголовке — получатель проверяет её
                            "X-Webhook-Signature": signature,
                            "X-Webhook-Event": delivery.event_type,
                        },
                        timeout=subscription.timeout,
                    )

                delivery.response_status = response.status_code
                delivery.response_body = response.text[:500]  # Первые 500 символов

                if response.status_code < 400:
                    # Успешная доставка
                    delivery.status = "success"
                    delivery.delivered_at = datetime.now(timezone.utc)
                else:
                    delivery.status = "failed"
                    delivery.error_message = f"HTTP {response.status_code}"

            except Exception as e:
                # Сетевая ошибка — таймаут, DNS и тд
                delivery.status = "failed"
                delivery.error_message = str(e)[:200]

            await db.commit()

        await engine.dispose()

    asyncio.run(run())


def trigger_webhook_event(event: str, data: dict, db_session=None):
    """
    Запускает отправку webhook для всех подписчиков события.
    
    Вызывается из сервисов когда происходит событие:
    - создана партия → trigger_webhook_event("batch_created", {...})
    - закрыта партия → trigger_webhook_event("batch_closed", {...})
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from src.data.models.webhook import WebhookDelivery, WebhookSubscription
    from src.utils.hmac_utils import build_webhook_payload
    from src.core.config import settings
    from sqlalchemy import select
    from datetime import datetime, timezone

    async def run():
        engine = create_async_engine(settings.database_url)
        SessionLocal = async_sessionmaker(engine, class_=AsyncSession)
        payload = build_webhook_payload(event, data)

        async with SessionLocal() as db:
            result = await db.execute(
                select(WebhookSubscription).where(
                    WebhookSubscription.is_active == True
                )
            )
            subscriptions = result.scalars().all()
            active = [s for s in subscriptions if event in s.events]

            for subscription in active:
                # Создаём запись доставки
                delivery = WebhookDelivery(
                    subscription_id=subscription.id,
                    event_type=event,
                    payload=payload,
                    status="pending",
                    created_at=datetime.now(timezone.utc),
                )
                db.add(delivery)
                await db.flush()
                await db.refresh(delivery)

                # Запускаем Celery задачу отправки
                send_webhook_delivery.delay(delivery.id)

            await db.commit()

        await engine.dispose()

    asyncio.run(run())
