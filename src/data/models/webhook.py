from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from src.data.models.base import Base, TimestampMixin

class WebhookSubscription(Base, TimestampMixin):
    __tablename__ = "webhook_subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # URL куда отправлять webhook
    url = Column(String, nullable=False)
    
    # Список событий на которые подписан ["batch_created", "batch_closed"]
    # JSON тип — хранит список как JSON в БД
    events = Column(JSON, nullable=False)
    
    # Секретный ключ для HMAC подписи запросов
    # Получатель проверяет подпись чтобы убедиться что запрос от нас
    secret_key = Column(String, nullable=False)
    
    # Активна ли подписка
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Сколько раз повторять при ошибке
    retry_count = Column(Integer, default=3, nullable=False)
    
    # Таймаут ожидания ответа в секундах
    timeout = Column(Integer, default=10, nullable=False)

    # История доставок
    deliveries = relationship("WebhookDelivery", back_populates="subscription")


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # К какой подписке относится доставка
    subscription_id = Column(Integer, ForeignKey("webhook_subscriptions.id"), nullable=False)
    
    # Тип события (например "batch_created")
    event_type = Column(String, nullable=False)
    
    # Данные которые отправили
    payload = Column(JSON, nullable=False)

    # Статус: "pending" → "success" или "failed"
    status = Column(String, nullable=False, default="pending")
    
    # Сколько попыток было сделано
    attempts = Column(Integer, default=0, nullable=False)
    
    # Ответ от получателя
    response_status = Column(Integer, nullable=True)   # HTTP статус код
    response_body = Column(String, nullable=True)      # Тело ответа
    error_message = Column(String, nullable=True)      # Сообщение об ошибке

    created_at = Column(DateTime(timezone=True), nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    subscription = relationship("WebhookSubscription", back_populates="deliveries")
