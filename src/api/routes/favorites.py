from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from uuid import UUID
from pydantic import BaseModel

from src.core.database import get_async_session
from src.api.models.favorite import Favorite
from src.api.models.bookdb import Book
from src.api.schemas.books import BookResponse
from src.api.routes.users import get_current_user_email

router = APIRouter(tags=["Favorites"], redirect_slashes=False)


class FavoriteAddRequest(BaseModel):
    book_id: UUID


@router.post("/me", status_code=201)
async def add_to_favorites(
        data: FavoriteAddRequest,
        user_email: str = Depends(get_current_user_email),
        db: AsyncSession = Depends(get_async_session)
):
    book_id = data.book_id

    q = await db.execute(select(Book).where(Book.id == book_id))
    book = q.scalar_one_or_none()
    if not book:
        raise HTTPException(404, "Book not found")

    q = await db.execute(
        select(Favorite).where(
            Favorite.user_email == user_email,
            Favorite.book_id == book_id
        )
    )
    if q.scalar_one_or_none():
        return {"status": "already_exists"}

    fav = Favorite(user_email=user_email, book_id=book_id)
    db.add(fav)
    await db.commit()
    return {"status": "added"}


@router.get("/me", response_model=list[BookResponse])
async def get_my_favorites(
        user_email: str = Depends(get_current_user_email),
        db: AsyncSession = Depends(get_async_session)
):
    q = await db.execute(
        select(Book)
        .join(Favorite, Favorite.book_id == Book.id)
        .where(Favorite.user_email == user_email)
    )
    return q.scalars().all()


@router.delete("/me/{book_id}", status_code=204)
async def remove_favorite(
        book_id: UUID,
        user_email: str = Depends(get_current_user_email),
        db: AsyncSession = Depends(get_async_session)
):
    await db.execute(
        delete(Favorite).where(
            Favorite.user_email == user_email,
            Favorite.book_id == book_id
        )
    )
    await db.commit()


@router.delete("/me", status_code=204)
async def clear_favorites(
        user_email: str = Depends(get_current_user_email),
        db: AsyncSession = Depends(get_async_session)
):
    await db.execute(
        delete(Favorite).where(Favorite.user_email == user_email)
    )
    await db.commit()


@router.get("/me/count")
async def count_favorites(
        user_email: str = Depends(get_current_user_email),
        db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(
        select(Favorite).where(Favorite.user_email == user_email)
    )
    items = result.scalars().all()
    return {"count": len(items)}
