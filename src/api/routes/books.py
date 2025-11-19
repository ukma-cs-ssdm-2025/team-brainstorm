from fastapi import APIRouter, HTTPException
from sqlalchemy.future import select
from uuid import UUID

from src.core.database import SessionLocal
from src.api.models.bookdb import Book
from src.api.schemas.books import BookCreate, BookUpdate, BookResponse

router = APIRouter(tags=["Books"])




# ==========================
# 📚 Отримати всі книги
# ==========================
@router.get("/", response_model=list[BookResponse])
async def get_books():
    async with SessionLocal() as db:
        result = await db.execute(select(Book))
        return result.scalars().all()


# ==========================
# 🔍 Отримати книгу за ID
# ==========================
@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: UUID):
    async with SessionLocal() as db:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()

        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        return book


# ==========================
# ➕ Створити книгу
# ==========================
@router.post("/", response_model=BookResponse)
async def create_book(data: BookCreate):
    async with SessionLocal() as db:
        new_book = Book(**data.dict())
        db.add(new_book)
        await db.commit()
        await db.refresh(new_book)
        return new_book


# ==========================
# ✏️ Оновити книгу
# ==========================
@router.put("/{book_id}", response_model=BookResponse)
async def update_book(book_id: UUID, data: BookUpdate):
    async with SessionLocal() as db:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()

        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        for key, value in data.dict(exclude_unset=True).items():
            setattr(book, key, value)

        await db.commit()
        await db.refresh(book)
        return book


# ==========================
# ❌ Видалити книгу
# ==========================
@router.delete("/{book_id}")
async def delete_book(book_id: UUID):
    async with SessionLocal() as db:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()

        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        await db.delete(book)
        await db.commit()

        return {"status": "deleted"}
