from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel, conint
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from src.core.database import get_async_session
from src.api.models.bookdb import Book
from src.api.models.review import Review
from src.api.models.user import User
from src.api.routes.users import get_current_user_email


router = APIRouter(tags=["Reviews"])


# ---------- SCHEMAS ----------


class ReviewCreate(BaseModel):
    rating: conint(ge=1, le=5)
    comment: Optional[str] = ""


class ReviewOut(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str
    rating: int
    comment: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class ReviewsListOut(BaseModel):
    items: List[ReviewOut]
    count: int
    average_rating: float


# ---------- HELPERS ----------


async def ensure_book_exists(session: AsyncSession, book_id: UUID):
    result = await session.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(404, "Book not found")


async def get_user_by_email(session: AsyncSession, email: str) -> User:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    return user


def serialize_review(review: Review, user_email: str) -> dict:
    return {
        "id": review.id,
        "user_id": review.user_id,
        "user_email": user_email,
        "rating": review.rating,
        "comment": review.comment,
        "created_at": review.created_at,
    }


# ---------- ROUTES ----------


@router.post("/books/{book_id}/reviews", response_model=ReviewOut, status_code=201)
async def add_review(
        book_id: UUID,
        payload: ReviewCreate,
        user_email: str = Depends(get_current_user_email),
        session: AsyncSession = Depends(get_async_session),
):
    """Додає новий відгук для книги."""

    await ensure_book_exists(session, book_id)
    user = await get_user_by_email(session, user_email)

    review = Review(
        id=uuid4(),
        user_id=user.id,
        book_id=book_id,
        rating=payload.rating,
        comment=payload.comment or "",
        created_at=datetime.utcnow(),
    )

    session.add(review)
    await session.commit()
    await session.refresh(review)

    return serialize_review(review, user.email)


@router.get("/books/{book_id}/reviews", response_model=ReviewsListOut)
async def list_reviews(
        book_id: UUID,
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
        session: AsyncSession = Depends(get_async_session),
):
    """Список відгуків та статистика."""

    await ensure_book_exists(session, book_id)

    result = await session.execute(
        select(Review)
        .options(selectinload(Review.user))
        .where(Review.book_id == book_id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    reviews = result.scalars().all()

    stats_q = await session.execute(
        select(
            func.count(Review.id),
            func.coalesce(func.avg(Review.rating), 0.0)
        ).where(Review.book_id == book_id)
    )
    count, avg = stats_q.one()

    items = [
        serialize_review(review, review.user.email if review.user else "")
        for review in reviews
    ]

    return {
        "items": items,
        "count": count,
        "average_rating": float(avg),
    }


@router.delete("/books/reviews/{review_id}", status_code=204)
async def remove_review(
        review_id: UUID,
        session: AsyncSession = Depends(get_async_session),
):
    """Видаляє відгук."""

    result = await session.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(404, "Review not found")

    await session.delete(review)
    await session.commit()

    return None
