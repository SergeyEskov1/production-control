from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class WebhookCreate(BaseModel):
    url: str
    events: list[str]
    secret_key: str
    retry_count: int = 3
    timeout: int = 10


class WebhookUpdate(BaseModel):
    is_active: Optional[bool] = None
    retry_count: Optional[int] = None
    timeout: Optional[int] = None


class WebhookResponse(BaseModel):
    id: int
    url: str
    events: list[str]
    is_active: bool
    retry_count: int
    timeout: int
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookDeliveryResponse(BaseModel):
    id: int
    event_type: str
    status: str
    attempts: int
    response_status: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    delivered_at: Optional[datetime] = None

    class Config:
        from_attributes = True
