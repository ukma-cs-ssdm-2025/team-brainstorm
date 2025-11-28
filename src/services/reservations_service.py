from datetime import date
from uuid import UUID, uuid4
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.user import User
from src.api.models.bookdb import Book
from src.api.models.reservation import Reservation


async def create_reservation_for_user(
        session: AsyncSession,
        user_id: UUID,        # ✅ UUID
        book_id: UUID,        # ✅ UUID
        until_date=None
):
    # 1. Перевіряємо користувача
    user_stmt = select(User).where(User.id == user_id)
    user_res = await session.execute(user_stmt)
    user = user_res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 2. Перевіряємо книгу
    book_stmt = select(Book).where(Book.id == book_id)
    book_res = await session.execute(book_stmt)
    book = book_res.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    # 3. Перевіряємо доступність
    available = book.total_copies - book.reserved_count
    if available <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No copies available"
        )

    # 4. Створюємо резервацію
    reservation = Reservation(
        id=uuid4(),
        user_id=user_id,
        book_id=book_id,
        from_date=date.today(),
        until=until_date
    )

    session.add(reservation)

    # 5. Оновлюємо лічильник
    book.reserved_count += 1

    await session.commit()
    await session.refresh(reservation)

    return reservation
