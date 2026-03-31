from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.core.config import settings

# Асинхронный движок SQLAlchemy
# echo=True — выводит все SQL запросы в консоль (удобно при разработке)
# pool_pre_ping=True — проверяет соединение перед каждым запросом
engine = create_async_engine(
    settings.database_url,
    echo=True,
    pool_pre_ping=True,
)

# Фабрика сессий — каждый запрос к API получает свою сессию
# expire_on_commit=False — объекты остаются доступны после commit
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency для FastAPI — автоматически открывает и закрывает сессию
# Используется в роутерах через Depends(get_db)
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
