# Импортируем все модели чтобы Alembic их видел при генерации миграций
from src.data.models.base import Base
from src.data.models.work_center import WorkCenter
from src.data.models.batch import Batch
from src.data.models.product import Product
from src.data.models.webhook import WebhookSubscription, WebhookDelivery
