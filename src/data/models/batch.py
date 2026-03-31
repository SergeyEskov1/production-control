from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from src.data.models.base import Base, TimestampMixin

class Batch(Base, TimestampMixin):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Статус закрытия партии
    # is_closed=True означает что смена завершена
    is_closed = Column(Boolean, default=False, nullable=False)
    # Время закрытия — null пока партия открыта
    closed_at = Column(DateTime(timezone=True), nullable=True)

    # Описание задания из 1С
    task_description = Column(String, nullable=False)
    
    # Внешний ключ на рабочий центр
    work_center_id = Column(Integer, ForeignKey("work_centers.id"), nullable=False)
    
    # Смена (например "1 смена")
    shift = Column(String, nullable=False)
    
    # Бригада (например "Бригада Иванова")
    team = Column(String, nullable=False)

    # Номер партии и дата — вместе уникальны
    # Нельзя создать две партии с одним номером в одну дату
    batch_number = Column(Integer, nullable=False, index=True)
    batch_date = Column(Date, nullable=False, index=True)

    # Что производим
    nomenclature = Column(String, nullable=False)
    ekn_code = Column(String, nullable=False)

    # Временные рамки смены
    shift_start = Column(DateTime(timezone=True), nullable=False)
    shift_end = Column(DateTime(timezone=True), nullable=False)

    # Связи
    # lazy="selectin" — автоматически подгружает связанные объекты
    work_center = relationship("WorkCenter", back_populates="batches")
    products = relationship("Product", back_populates="batch", lazy="selectin")

    __table_args__ = (
        # Составной уникальный индекс — номер+дата должны быть уникальны
        UniqueConstraint("batch_number", "batch_date", name="uq_batch_number_date"),
        # Индекс для быстрой фильтрации по статусу закрытия
        Index("idx_batch_closed", "is_closed"),
        # Индекс для поиска по временным рамкам смены
        Index("idx_batch_shift_times", "shift_start", "shift_end"),
    )

    def __repr__(self):
        return f"<Batch #{self.batch_number} {self.batch_date}>"
