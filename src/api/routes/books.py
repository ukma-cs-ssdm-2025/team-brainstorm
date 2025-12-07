import uuid
from uuid import UUID

from src.core.database import SessionLocal, async_session_maker
from src.api.models.bookdb import Book
from src.api.schemas.books import BookCreate, BookUpdate, BookResponse

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Якщо у тебе async_session_maker і SessionLocal у src.core.database:
from src.core.database import get_async_session

router = APIRouter(tags=["Books"])

@router.get("/search", response_model=list[BookResponse])
async def search_books(
        genres: list[str] = Query(default=[]),
        session: AsyncSession = Depends(get_async_session)
):
    query = select(Book)

    if genres:
        query = query.where(Book.genres.overlap(genres))

    result = await session.execute(query)
    books = result.scalars().all()

    return [BookResponse.from_orm(b) for b in books]



@router.get("/", response_model=list[BookResponse])
async def get_books():
    async with async_session_maker() as session:
        result = await session.execute(select(Book))
        books = result.scalars().all()
        return [BookResponse.from_orm(b) for b in books]


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: UUID):
    async with SessionLocal() as db:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()

        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        return BookResponse.from_orm(book)


@router.post("/", response_model=BookResponse)
async def create_book(data: BookCreate):
    async with SessionLocal() as db:
        new_book = Book(**data.dict())
        db.add(new_book)
        await db.commit()
        await db.refresh(new_book)
        return BookResponse.from_orm(new_book)



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
        return BookResponse.from_orm(book)


