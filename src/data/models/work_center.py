from sqlalchemy import Column, Integer, String, Index
from sqlalchemy.orm import relationship
from src.data.models.base import Base, TimestampMixin

class WorkCenter(Base, TimestampMixin):
    __tablename__ = "work_centers"

    # Первичный ключ — автоинкремент
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Уникальный идентификатор РЦ (например "RC-001")
    # unique=True — не может быть двух РЦ с одним идентификатором
    # index=True — быстрый поиск по этому полю
    identifier = Column(String, unique=True, nullable=False, index=True)
    
    # Человекочитаемое название (например "Цех №1")
    name = Column(String, nullable=False)

    # Связь один-ко-многим: один РЦ — много партий
    # back_populates — обратная ссылка из модели Batch
    batches = relationship("Batch", back_populates="work_center")

    def __repr__(self):
        return f"<WorkCenter {self.identifier}: {self.name}>"
