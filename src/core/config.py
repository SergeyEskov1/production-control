from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # База данных
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/production_control"
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    
    # Celery
    celery_broker_url: str = "amqp://admin:admin@rabbitmq:5672//"
    celery_result_backend: str = "redis://redis:6379/1"
    
    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False

    class Config:
        # Читаем значения из .env файла
        # Если переменная есть в .env — берём оттуда
        # Если нет — используем default значение выше
        env_file = ".env"
        case_sensitive = False

# Создаём один экземпляр настроек на всё приложение
# Импортируем его везде где нужны настройки: from src.core.config import settings
settings = Settings()
