from src.celery_app import app


@app.task
def auto_close_expired_batches():
    """
    Автоматически закрывает партии у которых shift_end < now().
    
    Запускается каждый день в 01:00 через Celery Beat.
    Бизнес логика: если смена закончилась — партия должна быть закрыта.
    """
    import asyncio
    from datetime import datetime, timezone
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import select
    from src.data.models.batch import Batch
    from src.core.config import settings

    async def run():
        engine = create_async_engine(settings.database_url)
        SessionLocal = async_sessionmaker(engine, class_=AsyncSession)
        now = datetime.now(timezone.utc)
        closed_count = 0

        async with SessionLocal() as db:
            # Ищем открытые партии у которых время смены уже прошло
            result = await db.execute(
                select(Batch).where(
                    Batch.is_closed == False,
                    Batch.shift_end < now,
                )
            )
            batches = result.scalars().all()

            for batch in batches:
                batch.is_closed = True
                batch.closed_at = now
                closed_count += 1

            await db.commit()

        await engine.dispose()
        return {"closed": closed_count, "timestamp": now.isoformat()}

    return asyncio.run(run())


@app.task
def cleanup_old_files():
    """
    Удаляет файлы старше 30 дней из MinIO.
    
    Запускается каждый день в 02:00.
    Освобождает место от старых отчётов и экспортов.
    """
    from datetime import datetime, timezone, timedelta
    from src.storage.minio_service import minio_service, BUCKETS

    deleted_count = 0
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    for bucket in BUCKETS:
        files = minio_service.list_files(bucket)
        for obj in files:
            # last_modified — время последнего изменения файла
            if obj.last_modified and obj.last_modified < cutoff:
                minio_service.delete_file(bucket, obj.object_name)
                deleted_count += 1

    return {"deleted": deleted_count}


@app.task
def update_cached_statistics():
    """
    Обновляет кэшированную статистику в Redis.
    
    Запускается каждые 5 минут через Celery Beat.
    Считает агрегированную статистику и кладёт в Redis
    чтобы dashboard грузился мгновенно из кэша.
    """
    import asyncio
    import json
    from datetime import datetime, timezone
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import select, func
    from src.data.models.batch import Batch
    from src.data.models.product import Product
    from src.core.config import settings
    import redis

    async def run():
        engine = create_async_engine(settings.database_url)
        SessionLocal = async_sessionmaker(engine, class_=AsyncSession)

        async with SessionLocal() as db:
            # Считаем статистику одним запросом
            total_batches = await db.scalar(select(func.count(Batch.id)))
            active_batches = await db.scalar(
                select(func.count(Batch.id)).where(Batch.is_closed == False)
            )
            total_products = await db.scalar(select(func.count(Product.id)))
            aggregated_products = await db.scalar(
                select(func.count(Product.id)).where(Product.is_aggregated == True)
            )

        await engine.dispose()

        stats = {
            "total_batches": total_batches or 0,
            "active_batches": active_batches or 0,
            "closed_batches": (total_batches or 0) - (active_batches or 0),
            "total_products": total_products or 0,
            "aggregated_products": aggregated_products or 0,
            "aggregation_rate": round(
                (aggregated_products or 0) / (total_products or 1) * 100, 2
            ),
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }

        # Сохраняем в Redis на 6 минут (чуть больше чем интервал задачи)
        r = redis.from_url(settings.redis_url)
        r.setex("dashboard_stats", 360, json.dumps(stats))

        return stats

    return asyncio.run(run())


@app.task
def retry_failed_webhooks():
    """
    Повторная отправка неудачных webhook доставок.
    
    Запускается каждые 15 минут.
    Находит доставки со статусом 'failed' и пробует отправить снова.
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import select
    from src.data.models.webhook import WebhookDelivery
    from src.core.config import settings

    async def run():
        engine = create_async_engine(settings.database_url)
        SessionLocal = async_sessionmaker(engine, class_=AsyncSession)

        async with SessionLocal() as db:
            result = await db.execute(
                select(WebhookDelivery).where(
                    WebhookDelivery.status == "failed",
                    WebhookDelivery.attempts < 3,  # Не более 3 попыток
                ).limit(100)
            )
            deliveries = result.scalars().all()
            retried = len(deliveries)

            # Сбрасываем статус на pending — задача отправки подхватит
            for delivery in deliveries:
                delivery.status = "pending"

            await db.commit()

        await engine.dispose()
        return {"retried": retried}

    return asyncio.run(run())
