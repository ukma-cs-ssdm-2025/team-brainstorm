from uuid import uuid4
from datetime import datetime
from statistics import mean
from typing import Tuple, List, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.user import User
from src.api.models.bookdb import Book
from src.api.models.review import Review


def _validate_rating(rating: int):
    if not (1 <= rating <= 5):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Rating must be between 1 and 5"
        )


async def create_review_for_book(
        session: AsyncSession,
        user_id: int,
        book_id: int,
        rating: int,
        comment: str | None = None
):
    """Створює відгук для книги через ORM."""
    _validate_rating(rating)

    # Перевіряємо чи існує книга
    book_res = await session.execute(select(Book).where(Book.id == book_id))
    book = book_res.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    # Перевіряємо чи існує користувач
    user_res = await session.execute(select(User).where(User.id == user_id))
    user = user_res.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    review = Review(
        id=uuid4(),
        book_id=book_id,
        user_id=user_id,
        rating=rating,
        comment=comment or "",
        created_at=datetime.utcnow(),
    )

    session.add(review)
    await session.commit()
    await session.refresh(review)

    return review


async def get_reviews_for_book(
        session: AsyncSession,
        book_id: int,
        skip: int = 0,
        limit: int = 50
) -> Tuple[List[Review], Dict[str, Any]]:
    """Отримує список відгуків + статистику."""
    # Перевіряємо наявність книги
    book_res = await session.execute(select(Book).where(Book.id == book_id))
    book = book_res.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    # Отримуємо пагіновані відгуки
    reviews_res = await session.execute(
        select(Review)
        .where(Review.book_id == book_id)
        .offset(skip)
        .limit(limit)
        .order_by(Review.created_at.desc())
    )
    reviews = reviews_res.scalars().all()

    # Підраховуємо count і average
    stats_res = await session.execute(
        select(
            func.count(Review.id),
            func.avg(Review.rating)
        ).where(Review.book_id == book_id)
    )
    count, avg = stats_res.one()

    stats = {
        "count": count,
        "average_rating": round(float(avg), 2) if avg else 0.0
    }

    return reviews, stats


async def delete_review(session: AsyncSession, review_id):
    """Видаляє відгук із PostgreSQL."""
    # Перевіряємо чи існує review
    review_res = await session.execute(select(Review).where(Review.id == review_id))
    review = review_res.scalar_one_or_none()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    await session.delete(review)
    await session.commit()
