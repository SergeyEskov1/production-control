from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ProductCreate(BaseModel):
    """Схема для создания продукции"""
    unique_code: str   # Уникальный код со штрихкода
    batch_id: int      # К какой партии привязываем


class ProductResponse(BaseModel):
    """Схема ответа для продукции"""
    id: int
    unique_code: str
    batch_id: int
    is_aggregated: bool
    aggregated_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AggregateRequest(BaseModel):
    """Схема для агрегации продукции"""
    # Список уникальных кодов для агрегации
    unique_codes: list[str]
