from uuid import uuid4
from datetime import datetime
from statistics import mean
from typing import List, Dict, Any, Tuple
from fastapi import HTTPException, status
from src.core.database import BOOKS, USERS, REVIEWS, DB_LOCK


def _validate_rating(rating: int):
    """Перевіряє, що рейтинг у діапазоні 1–5."""
    if rating < 1 or rating > 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Rating must be between 1 and 5"
        )


def create_review_for_book(user_id, book_id, rating: int, comment: str | None = None) -> Dict[str, Any]:
    """
    Створює відгук для книги:
    - перевіряє існування книги та користувача,
    - перевіряє валідність рейтингу,
    - зберігає відгук у REVIEWS.
    """
    _validate_rating(rating)
    with DB_LOCK:
        if book_id not in BOOKS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
        if user_id not in USERS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        review_id = uuid4()
        review = {
            "id": review_id,
            "book_id": book_id,
            "user_id": user_id,
            "rating": int(rating),
            "comment": comment or "",
            "created_at": datetime.utcnow().isoformat()
        }
        REVIEWS[review_id] = review
        return review


def get_reviews_for_book(book_id, skip: int = 0, limit: int = 50) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Отримує список відгуків для книги.
    Повертає:
      - items (список відгуків з пагінацією),
      - stats (кількість відгуків та середній рейтинг).
    """
    with DB_LOCK:
        if book_id not in BOOKS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
        book_reviews = [r for r in REVIEWS.values() if r["book_id"] == book_id]
        paged = book_reviews[skip: skip + limit]
        stats = {
            "count": len(book_reviews),
            "average_rating": round(mean([r["rating"] for r in book_reviews]), 2) if book_reviews else 0.0
        }
        return paged, stats


def delete_review(review_id):
    """Видаляє відгук за його ID."""
    with DB_LOCK:
        if review_id not in REVIEWS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
        del REVIEWS[review_id]
