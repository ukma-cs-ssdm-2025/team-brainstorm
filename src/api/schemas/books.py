from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID


class BookBase(BaseModel):
    title: str
    author: str
    isbn: str
    total_copies: int
    genres: List[str] = []


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    total_copies: Optional[int] = None
    genres: Optional[List[str]] = None


class BookResponse(BookBase):
    id: UUID
    reserved_count: int = 0

    class Config:
        orm_mode = True
