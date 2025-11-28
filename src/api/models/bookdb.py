import uuid
from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from src.core.database import Base
from sqlalchemy.orm import relationship

class Book(Base):
    __tablename__ = "books"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    isbn = Column(String, unique=True, nullable=False)

    genres = Column(ARRAY(String), default=[])
    total_copies = Column(Integer, default=1)
    reserved_count = Column(Integer, default=0)

    cover_image = Column(String, nullable=True)

    reviews = relationship("Review", back_populates="book")
