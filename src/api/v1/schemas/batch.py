from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional
from src.api.v1.schemas.product import ProductResponse

class BatchCreate(BaseModel):
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
        populate_by_name = True


class BatchUpdate(BaseModel):
    is_closed: Optional[bool] = None
    task_description: Optional[str] = None
    shift: Optional[str] = None
    team: Optional[str] = None
    nomenclature: Optional[str] = None


class BatchResponse(BaseModel):
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
    created_at: Optional[datetime] = None
    products: list[ProductResponse] = []

    class Config:
        from_attributes = True


class BatchListResponse(BaseModel):
    items: list[BatchResponse]
    total: int
    offset: int
    limit: int
