import os
from celery import Celery
from celery.schedules import crontab

app = Celery(
    "production_control",
    broker=os.getenv("CELERY_BROKER_URL", "amqp://admin:admin@rabbitmq:5672//"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1"),
    # Автоматически находит задачи в этих модулях
    include=[
        "src.tasks.aggregation",
        "src.tasks.reports",
        "src.tasks.scheduled",
    ],
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Результаты хранятся 24 часа
    result_expires=86400,
    # Retry соединения при старте
    broker_connection_retry_on_startup=True,

    # ===== Расписание задач (Celery Beat) =====
    beat_schedule={
        # Закрытие просроченных партий — каждый день в 01:00
        "auto-close-expired-batches": {
            "task": "src.tasks.scheduled.auto_close_expired_batches",
            "schedule": crontab(hour=1, minute=0),
        },
        # Очистка старых файлов — каждый день в 02:00
        "cleanup-old-files": {
            "task": "src.tasks.scheduled.cleanup_old_files",
            "schedule": crontab(hour=2, minute=0),
        },
        # Обновление статистики — каждые 5 минут
        "update-statistics": {
            "task": "src.tasks.scheduled.update_cached_statistics",
            "schedule": crontab(minute="*/5"),
        },
        # Повторная отправка webhooks — каждые 15 минут
        "retry-failed-webhooks": {
            "task": "src.tasks.scheduled.retry_failed_webhooks",
            "schedule": crontab(minute="*/15"),
        },
    },
)
