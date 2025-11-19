from sqlalchemy.future import select
from src.core.database import SessionLocal
from src.api.models.bookdb import Book


async def get_books():
    async with SessionLocal() as db:
        result = await db.execute(select(Book))
        return result.scalars().all()


async def get_book_by_id(book_id: int):
    async with SessionLocal() as db:
        result = await db.execute(select(Book).where(Book.id == book_id))
        return result.scalar_one_or_none()


async def create_book(data: dict):
    async with SessionLocal() as db:
        book = Book(**data)
        db.add(book)
        await db.commit()
        await db.refresh(book)
        return book


async def delete_book(book_id: int):
    async with SessionLocal() as db:
        book = await get_book_by_id(book_id)
        if not book:
            return None
        await db.delete(book)
        await db.commit()
        return True
