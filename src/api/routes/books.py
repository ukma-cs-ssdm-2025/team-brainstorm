from fastapi import APIRouter, Query
from typing import List
from uuid import UUID
from src.core.database import BOOKS
from pydantic import BaseModel, Field, constr


router = APIRouter()


class BookOut(BaseModel):
    id: UUID
    isbn: constr(min_length=10, max_length=17)
    title: str
    author: str
    total_copies: int
    reserved_count: int = Field(0)


@router.get("/", response_model=List[BookOut])
def list_books(available_only: bool = Query(False)):
    results = []
    for b in BOOKS.values():
        # Якщо потрібно показати лише доступні книги
        if available_only and (b["total_copies"] - b.get("reserved_count", 0)) <= 0:
            continue
        results.append(BookOut(**b))
    return results
