from fastapi import APIRouter, HTTPException, status, Response, Depends, Header
from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.api.models.user import User
from src.api.models.bookdb import Book
from src.api.models.reservation import Reservation


router = APIRouter(prefix="/reservations", tags=["Reservations"])


class ReservationCreate(BaseModel):
    user_id: UUID | None = None
    book_id: UUID
    until: date | None = None


class ReservationOut(BaseModel):
    id: UUID
    user_id: UUID
    book_id: UUID
    from_date: date
    until: date | None = None


# --------------------------
#  Helper: get user email
# --------------------------

async def get_user_email(
        x_user_email: str | None = Header(None, alias="X-User-Email")
) -> str | None:
    return x_user_email.strip().lower() if x_user_email else None


# --------------------------
#  Create reservation
# --------------------------

@router.post("/", response_model=ReservationOut, status_code=status.HTTP_201_CREATED)
async def create_reservation(
        payload: ReservationCreate,
        user_email: str | None = Depends(get_user_email),
        session: AsyncSession = Depends(get_async_session)
):
    # USER ID autoselect via email
    user_id = payload.user_id

    if user_id is None:
        if not user_email:
            raise HTTPException(400, "Provide user_id or X-User-Email header")

        # find user by email
        result = await session.execute(select(User).where(User.email == user_email))
        user = result.scalar_one_or_none()

        # create user if not exists
        if not user:
            user = User(id=uuid4(), email=user_email)
            session.add(user)
            await session.commit()

        user_id = user.id
    else:
        # check user exists
        result = await session.execute(select(User).where(User.id == user_id))
        if result.scalar_one_or_none() is None:
            raise HTTPException(404, "User not found")

    # check book exists
    result = await session.execute(select(Book).where(Book.id == payload.book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(404, "Book not found")

    # create reservation
    reservation = Reservation(
        id=uuid4(),
        user_id=user_id,
        book_id=payload.book_id,
        from_date=date.today(),
        until=payload.until,
    )

    session.add(reservation)
    await session.commit()

    return ReservationOut(
        id=reservation.id,
        user_id=reservation.user_id,
        book_id=reservation.book_id,
        from_date=reservation.from_date,
        until=reservation.until,
    )


# --------------------------
#  Cancel reservation
# --------------------------

@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_reservation(
        reservation_id: UUID,
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Reservation).where(Reservation.id == reservation_id))
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(404, "Reservation not found")

    await session.delete(reservation)
    await session.commit()

    return Response(status_code=204)
