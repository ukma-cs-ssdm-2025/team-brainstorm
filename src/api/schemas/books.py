from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from pydantic import validator


class BookBase(BaseModel):
    title: str
    author: str
    isbn: str
    total_copies: int
    genres: List[str] = []
    cover_image: Optional[str] = None


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    total_copies: Optional[int] = None
    genres: Optional[List[str]] = None


class BookResponse(BaseModel):
    id: UUID
    title: str
    author: str
    isbn: str
    genres: List[str]
    total_copies: int
    reserved_count: int
    cover_image: str | None = None

    model_config = {
        "from_attributes": True
    }
