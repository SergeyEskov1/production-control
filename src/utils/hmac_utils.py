import hmac
import hashlib
import json
from datetime import datetime, timezone


def generate_signature(payload: dict, secret_key: str) -> str:
    """
    Генерирует HMAC-SHA256 подпись для webhook payload.
    
    HMAC — это способ проверить что запрос пришёл именно от нас.
    Получатель webhook знает secret_key и может проверить подпись.
    Если подпись не совпадает — запрос поддельный.
    """
    # Конвертируем payload в строку с фиксированным порядком ключей
    # sort_keys=True важен — одинаковый словарь всегда даёт одну строку
    payload_str = json.dumps(payload, sort_keys=True, default=str)
    
    # Создаём HMAC подпись
    # secret_key.encode() — переводим строку в байты
    # payload_str.encode() — то же самое для payload
    # digestmod=hashlib.sha256 — используем алгоритм SHA256
    signature = hmac.new(
        secret_key.encode(),
        payload_str.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()  # hexdigest() — возвращает подпись как hex строку
    
    return f"sha256={signature}"


def verify_signature(payload: dict, secret_key: str, signature: str) -> bool:
    """
    Проверяет по
cat > src/api/v1/schemas/webhook.py << 'EOF'
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional


class WebhookCreate(BaseModel):
    """Схема создания подписки."""
    url: str                          # URL куда отправлять
    events: list[str]                 # Список событий
    secret_key: str                   # Ключ для HMAC подписи
    retry_count: int = 3              # Количество попыток
    timeout: int = 10                 # Таймаут в секундах


class WebhookUpdate(BaseModel):
    """Схема обновления подписки."""
    is_active: Optional[bool] = None
    retry_count: Optional[int] = None
    timeout: Optional[int] = None


class WebhookResponse(BaseModel):
    """Схема ответа для подписки."""
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
    """Схема ответа для истории доставок."""
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
