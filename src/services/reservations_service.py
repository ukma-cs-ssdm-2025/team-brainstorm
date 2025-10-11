from uuid import uuid4
from datetime import date
from fastapi import HTTPException, status
from src.core.database import BOOKS, RESERVATIONS, DB_LOCK


def create_reservation_for_user(user_id, book_id, until_date=None):
    """
    Створює нову резервацію для користувача.
    Перевіряє, чи існує книга і чи є вільні копії.
    """
    with DB_LOCK:
        book = BOOKS.get(book_id)
        if not book:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

        available = book["total_copies"] - book.get("reserved_count", 0)
        if available <= 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No copies available")

        res_id = uuid4()
        reservation = {
            "id": res_id,
            "user_id": user_id,
            "book_id": book_id,
            "from_date": date.today(),
            "until": until_date,
        }

        RESERVATIONS[res_id] = reservation
        book["reserved_count"] = book.get("reserved_count", 0) + 1

        return reservation
