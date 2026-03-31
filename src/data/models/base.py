from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, DateTime
from datetime import datetime, timezone

# Базовый класс для всех моделей
# Все модели наследуются от Base — SQLAlchemy знает о них
class Base(DeclarativeBase):
    pass

# Миксин с полями created_at и updated_at
# Добавляем его к моделям которым нужны эти поля
class TimestampMixin:
    # Время создания — устанавливается один раз при INSERT
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    # Время обновления — меняется при каждом UPDATE
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
