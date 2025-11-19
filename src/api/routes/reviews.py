from fastapi import APIRouter, Query, status, HTTPException, Depends
from pydantic import BaseModel, conint
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.core.database import get_async_session
from src.api.models.bookdb import Book
from src.api.models.review import Review
from src.api.models.user import User


router = APIRouter()


# ---------- SCHEMAS ----------

class ReviewCreate(BaseModel):
    user_id: UUID
    rating: conint(ge=1, le=5)
    comment: Optional[str] = ""


class ReviewOut(BaseModel):
    id: UUID
    user_id: UUID
    rating: int
    comment: str
    created_at: datetime


class ReviewsListOut(BaseModel):
    items: List[ReviewOut]
    count: int
    average_rating: float


# ---------- HELPERS ----------

async def ensure_book_exists(session: AsyncSession, book_id: UUID):
    res = await session.execute(select(Book).where(Book.id == book_id))
    book = res.scalar_one_or_none()
    if not book:
        raise HTTPException(404, "Book not found")


async def ensure_user_exists(session: AsyncSession, user_id: UUID):
    res = await session.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")


# ---------- ROUTES ----------


@router.post("/{book_id}/reviews", response_model=ReviewOut, status_code=201)
async def add_review(
        book_id: UUID,
        payload: ReviewCreate,
        session: AsyncSession = Depends(get_async_session),
):
    """Додає новий відгук для книги"""

    # Перевірки
    await ensure_book_exists(session, book_id)
    await ensure_user_exists(session, payload.user_id)

    # Створення
    review = Review(
        id=uuid4(),
        user_id=payload.user_id,
        book_id=book_id,
        rating=payload.rating,
        comment=payload.comment or "",
        created_at=datetime.utcnow(),
    )

    session.add(review)
    await session.commit()
    await session.refresh(review)

    return review


@router.get("/{book_id}/reviews", response_model=ReviewsListOut)
async def list_reviews(
        book_id: UUID,
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
        session: AsyncSession = Depends(get_async_session),
):
    """Список відгуків + статистика"""

    await ensure_book_exists(session, book_id)

    # Отримати список
    result = await session.execute(
        select(Review)
        .where(Review.book_id == book_id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    reviews = result.scalars().all()

    # Статистика
    stats_q = await session.execute(
        select(
            func.count(Review.id),
            func.coalesce(func.avg(Review.rating), 0.0)
        ).where(Review.book_id == book_id)
    )
    count, avg = stats_q.one()

    return {
        "items": reviews,
        "count": count,
        "average_rating": float(avg),
    }


@router.delete("/reviews/{review_id}", status_code=204)
async def remove_review(
        review_id: UUID,
        session: AsyncSession = Depends(get_async_session),
):
    """Видаляє відгук"""

    result = await session.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(404, "Review not found")

    await session.delete(review)
    await session.commit()

    return None
