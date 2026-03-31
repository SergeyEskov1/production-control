import os
from celery import Celery

# Создаём экземпляр Celery
# Первый аргумент — имя модуля (для именования задач)
# broker — RabbitMQ принимает задачи от API и раздаёт воркерам
# backend — Redis хранит результаты выполненных задач
app = Celery(
    "production_control",
    broker=os.getenv("CELERY_BROKER_URL", "amqp://admin:admin@rabbitmq:5672//"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1"),
)

# Настройки Celery
app.conf.update(
    # Формат сериализации задач и результатов
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    
    # Часовой пояс
    timezone="UTC",
    enable_utc=True,
    
    # Результаты хранятся 1 день (в секундах)
    result_expires=86400,
)
