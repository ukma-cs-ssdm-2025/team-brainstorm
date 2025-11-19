from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.reservation import Reservation
from src.api.models.bookdb import Book
from src.api.models.user import User


async def get_due_soon_reservations(
        session: AsyncSession,
        days_before: int = 2
):
    """
    Повертає список броней, у яких скоро завершується термін.
    JOIN: reservations → books → users
    """

    today = date.today()

    stmt = (
        select(Reservation, Book, User)
        .join(Book, Reservation.book_id == Book.id)
        .join(User, Reservation.user_id == User.id)
        .where(
            Reservation.until.is_not(None),
            Reservation.until - today <= timedelta(days=days_before)
        )
    )

    result = await session.execute(stmt)

    reminders = []
    for res, book, user in result.all():
        reminders.append({
            "reservation_id": str(res.id),
            "book_title": book.title,
            "user_email": user.email,
            "days_left": (res.until - today).days
        })

    return reminders


async def send_reminders(session: AsyncSession):
    """
    Імітація відправлення email-нагадувань.
    Можна замінити на реальний EmailService.
    """
    reminders = await get_due_soon_reservations(session)

    for r in reminders:
        print(f"[Reminder] {r['user_email']}, поверніть книгу "
              f"'{r['book_title']}' через {r['days_left']} днів.")

    return reminders
