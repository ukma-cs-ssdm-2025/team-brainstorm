from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.api.models.reservation import Reservation
from src.api.models.bookdb import Book

router = APIRouter(prefix="/reminders", tags=["Reminders"])


@router.get("/")
async def get_reminders(session: AsyncSession = Depends(get_async_session)):
    today = date.today()

    stmt = (
        select(Reservation, Book)
        .join(Book, Book.id == Reservation.book_id)
        .where(Reservation.until.is_not(None))
    )

    result = await session.execute(stmt)
    rows = result.all()

    reminders = []

    for res, book in rows:
        days_left = (res.until - today).days
        if days_left <= 2:
            reminders.append({
                "reservation_id": res.id,
                "book_title": book.title,
                "days_left": days_left
            })

    return reminders
