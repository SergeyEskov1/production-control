from src.celery_app import app
from datetime import datetime, timezone


@app.task(bind=True, max_retries=3)
def aggregate_products_batch(
    self,
    batch_id: int,
    unique_codes: list[str],
    user_id: int = None,
):
    """
    Асинхронная массовая агрегация продукции.
    
    Используется когда нужно агрегировать >100 единиц.
    bind=True — даёт доступ к self для retry и обновления прогресса.
    max_retries=3 — при ошибке попробует ещё 3 раза.
    
    Прогресс обновляется через self.update_state — 
    клиент может опрашивать GET /api/v1/tasks/{task_id}
    и видеть сколько уже обработано.
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import select
    from src.data.models.batch import Batch
    from src.data.models.product import Product
    from src.core.config import settings

    async def run():
        # Создаём отдельное подключение к БД для Celery задачи
        # Нельзя использовать подключение из FastAPI — они в разных процессах
        engine = create_async_engine(settings.database_url)
        SessionLocal = async_sessionmaker(engine, class_=AsyncSession)

        aggregated = 0
        failed = 0
        errors = []
        total = len(unique_codes)

        async with SessionLocal() as db:
            # Проверяем что партия существует
            result = await db.execute(
                select(Batch).where(Batch.id == batch_id)
            )
            batch = result.scalar_one_or_none()
            if not batch:
                return {
                    "success": False,
                    "error": f"Batch {batch_id} not found"
                }

            # Обрабатываем коды порциями по 50
            # Обновляем прогресс после каждой порции
            chunk_size = 50
            for i in range(0, total, chunk_size):
                chunk = unique_codes[i:i + chunk_size]

                for code in chunk:
                    result = await db.execute(
                        select(Product).where(Product.unique_code == code)
                    )
                    product = result.scalar_one_or_none()

                    if not product:
                        errors.append({"code": code, "reason": "not found"})
                        failed += 1
                        continue

                    if product.batch_id != batch_id:
                        errors.append({"code": code, "reason": "wrong batch"})
                        failed += 1
                        continue

                    if product.is_aggregated:
                        errors.append({"code": code, "reason": "already aggregated"})
                        failed += 1
                        continue

                    product.is_aggregated = True
                    product.aggregated_at = datetime.now(timezone.utc)
                    aggregated += 1

                await db.commit()

                # Обновляем прогресс — клиент видит через GET /tasks/{id}
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": min(i + chunk_size, total),
                        "total": total,
                        "progress": round((i + chunk_size) / total * 100),
                    }
                )

        await engine.dispose()
        return {
            "success": True,
            "total": total,
            "aggregated": aggregated,
            "failed": failed,
            "errors": errors[:50],  # Первые 50 ошибок
        }

    try:
        import asyncio
        return asyncio.run(run())
    except Exception as exc:
        # При ошибке — повторяем через 60 секунд
        raise self.retry(exc=exc, countdown=60)
