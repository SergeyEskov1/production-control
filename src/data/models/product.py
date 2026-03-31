from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from src.data.models.base import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Уникальный код продукции (например "12gRV60MMsn1")
    # Сканируется со штрихкода на производстве
    unique_code = Column(String, unique=True, nullable=False, index=True)
    
    # К какой партии относится продукт
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False, index=True)

    # Аггрегирована ли продукция (отсканирована и учтена)
    is_aggregated = Column(Boolean, default=False, nullable=False, index=True)
    # Время аггрегации — null пока не аггрегирована
    aggregated_at = Column(DateTime(timezone=True), nullable=True)

    # Время создания записи
    created_at = Column(DateTime(timezone=True), nullable=False)

    # Связь с партией
    batch = relationship("Batch", back_populates="products")

    __table_args__ = (
        # Составной индекс для быстрой выборки:
        # "все неаггрегированные продукты партии X"
        Index("idx_product_batch_aggregated", "batch_id", "is_aggregated"),
    )

    def __repr__(self):
        return f"<Product {self.unique_code}>"
