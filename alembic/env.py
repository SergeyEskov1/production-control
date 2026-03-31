import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Импортируем настройки приложения
from src.core.config import settings

# Импортируем ВСЕ модели — без этого Alembic не увидит таблицы
from src.data.models import Base
from src.data.models.work_center import WorkCenter
from src.data.models.batch import Batch
from src.data.models.product import Product
from src.data.models.webhook import WebhookSubscription, WebhookDelivery

# Конфиг из alembic.ini
config = context.config

# Настройка логирования из alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные всех моделей — Alembic сравнивает их с БД
# и генерирует нужные миграции
target_metadata = Base.metadata

# Подставляем URL базы из настроек приложения
# Это важно — не хардкодим URL в alembic.ini
config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    """Миграции без подключения к БД — генерирует SQL файл."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Асинхронные миграции — нужно для asyncpg драйвера."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Запуск асинхронных миграций."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
