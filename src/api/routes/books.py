from fastapi import APIRouter, Query, HTTPException, Header, status
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, constr
from src.core.database import BOOKS, DB_LOCK



router = APIRouter()


class BookOut(BaseModel):
    id: UUID
    isbn: constr(min_length=10, max_length=17)
    title: str
    author: str
    total_copies: int
    reserved_count: int = Field(0)
    genres: List[str] = Field(default_factory=list)

class BookUpdate(BaseModel):
    isbn: Optional[constr(min_length=10, max_length=17)] = None
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    year: Optional[int] = Field(None, ge=1400, le=2100)
    total_copies: Optional[int] = Field(None, ge=0)
    reserved_count: Optional[int] = Field(None, ge=0)
    genres: Optional[List[str]] = None

@router.get("/", response_model=List[BookOut])
def list_books(
        available_only: bool = Query(False),
        genres: Optional[List[str]] = Query(None),
):
    results = []
    for b in BOOKS.values():
        # Фільтр: лише доступні
        if available_only and (b["total_copies"] - b.get("reserved_count", 0)) <= 0:
            continue

        # Фільтр: жанри
        if genres:
            # нормалізуємо регістр
            book_genres = [g.lower() for g in b.get("genres", [])]
            if not any(g.lower() in book_genres for g in genres):
                continue

        results.append(BookOut(**b))

    return results


@router.patch("/{book_id}", response_model=BookOut)
def update_book(
        book_id: UUID,
        payload: BookUpdate,
        x_role: str = Header(..., alias="X-Role", description="user | librarian"),
):
    if x_role.lower() != "librarian":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only librarian can edit books")

    with DB_LOCK:
        book = BOOKS.get(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        # оновлюємо дозволені поля
        data = payload.dict(exclude_unset=True)
        for k, v in data.items():
            if v is None:
                continue
            # genres – зберігаємо як список рядків
            if k == "genres":
                book["genres"] = list(v)
            else:
                book[k] = v

        # інваріанти: reserved_count не може перевищувати total_copies
        if book.get("total_copies", 0) < book.get("reserved_count", 0):
            book["reserved_count"] = max(0, book["total_copies"])


        return BookOut(**book)
        
@router.get("/available_count")
def get_available_books_count() -> dict[str, int]:
    """
    Повертає кількість доступних (не зарезервованих) книг у бібліотеці.
    """
    with DB_LOCK:
        available_books = [
            book
            for book in BOOKS.values()
            if book.get("total_copies", 0) - book.get("reserved", 0) > 0
        ]
    return {"available_count": len(available_books)}

@router.get("/{book_id}", response_model=BookOut)
def get_book_by_id(
    book_id: UUID,
    include_availability: bool = Query(False, description="Include availability information")
):
    """
    Отримує детальну інформацію про книгу за ID.
    """
    with DB_LOCK:
        book = BOOKS.get(book_id)
        if not book:
            raise HTTPException(
                status_code=404, 
                detail=f"Book with ID {book_id} not found"
            )
        
        # Створюємо базовий об'єкт книги
        book_data = BookOut(**book)
        
        # Додаємо інформацію про доступність
        if include_availability:
            available_copies = book.get("total_copies", 0) - book.get("reserved_count", 0)
            book_data.available_copies = max(0, available_copies)
            book_data.is_available = available_copies > 0
        
        return book_data


