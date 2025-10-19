from fastapi import APIRouter, Query, status
from pydantic import BaseModel, conint
from typing import List, Optional
from uuid import UUID
from src.services.reviews_service import create_review_for_book, get_reviews_for_book, delete_review

# Роутер для роботи з відгуками
router = APIRouter(prefix="/books", tags=["reviews"])


# ----- Pydantic-схеми -----
class ReviewCreate(BaseModel):
    """Схема для створення нового відгуку"""
    user_id: UUID
    rating: conint(ge=1, le=5)
    comment: Optional[str] = ""


class ReviewOut(BaseModel):
    """Схема відгуку для відповіді"""
    id: UUID
    user_id: UUID
    rating: int
    comment: str
    created_at: str


class ReviewsListOut(BaseModel):
    """Схема списку відгуків + статистика"""
    items: List[ReviewOut]
    count: int
    average_rating: float


# ----- Ендпоінти -----
@router.post("/{book_id}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def add_review(book_id: UUID, payload: ReviewCreate):
    """Додає новий відгук для книги"""
    return create_review_for_book(
        user_id=payload.user_id,
        book_id=book_id,
        rating=payload.rating,
        comment=payload.comment or ""
    )


@router.get("/{book_id}/reviews", response_model=ReviewsListOut)
def list_reviews(book_id: UUID, skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200)):
    """Отримує список відгуків по книзі + статистику (кількість, середній рейтинг)"""
    items, stats = get_reviews_for_book(book_id, skip=skip, limit=limit)
    return {"items": items, **stats}


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_review(review_id: UUID):
    """Видаляє відгук"""
    delete_review(review_id)
    return None
