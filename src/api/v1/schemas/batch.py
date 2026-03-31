from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional
from src.api.v1.schemas.product import ProductResponse

# ===== ВХОДЯЩИЕ ДАННЫЕ (Request) =====

class BatchCreate(BaseModel):
    """Схема для создания партии — принимает данные из 1С"""
    
    # Поля с русскими именами из 1С — alias позволяет принимать
    # русские ключи в JSON и маппить их на английские поля модели
    is_closed: bool = Field(alias="СтатусЗакрытия", default=False)
    task_description: str = Field(alias="ПредставлениеЗаданияНаСмену")
    work_center_name: str = Field(alias="РабочийЦентр")
    shift: str = Field(alias="Смена")
    team: str = Field(alias="Бригада")
    batch_number: int = Field(alias="НомерПартии")
    batch_date: date = Field(alias="ДатаПартии")
    nomenclature: str = Field(alias="Номенклатура")
    ekn_code: str = Field(alias="КодЕКН")
    work_center_identifier: str = Field(alias="ИдентификаторРЦ")
    shift_start: datetime = Field(alias="ДатаВремяНачалаСмены")
    shift_end: datetime = Field(alias="ДатаВремяОкончанияСмены")

    class Config:
        # Разрешаем использовать и alias и оригинальное имя поля
        populate_by_name = True


class BatchUpdate(BaseModel):
    """Схема для обновления партии — все поля опциональны"""
    is_closed: Optional[bool] = None
    task_description: Optional[str] = None
    shift: Optional[str] = None
    team: Optional[str] = None
    nomenclature: Optional[str] = None


# ===== ИСХОДЯЩИЕ ДАННЫЕ (Response) =====

class BatchResponse(BaseModel):
    """Схема ответа — что возвращаем клиенту"""
    id: int
    is_closed: bool
    closed_at: Optional[datetime] = None
    task_description: str
    shift: str
    team: str
    batch_number: int
    batch_date: date
    nomenclature: str
    ekn_code: str
    shift_start: datetime
    shift_end: datetime
    created_at: datetime
    # Список продукции партии
    products: list[ProductResponse] = []

    class Config:
        # Позволяет создавать схему из ORM объекта (SQLAlchemy модели)
        from_attributes = True


class BatchListResponse(BaseModel):
    """Схема для списка партий с пагинацией"""
    items: list[BatchResponse]
    total: int
    offset: int
    limit: int
