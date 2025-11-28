# src/api/routes/reservations.py
from fastapi import APIRouter, HTTPException, status, Response, Depends, Header
from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from secrets import token_urlsafe

from src.core.database import get_async_session
from src.core.security import hash_password
from src.api.models.user import User, UserRole
from src.api.models.bookdb import Book
from src.api.models.reservation import Reservation

router = APIRouter()


# --------------------------
#  Schemas
# --------------------------

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
    # --------------------------
    #  Resolve user
    # --------------------------
    user_id = payload.user_id

    if user_id is None:
        if not user_email:
            raise HTTPException(status_code=400, detail="Provide user_id or X-User-Email header")

        result = await session.execute(select(User).where(User.email == user_email))
        user = result.scalar_one_or_none()

        if not user:
            # generate a random password and store its hash so DB NOT NULL constraints are satisfied
            random_password = token_urlsafe(16)
            pw_hash = hash_password(random_password)

            user = User(
                id=uuid4(),
                email=user_email,
                password_hash=pw_hash,
                role=UserRole.user
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        user_id = user.id
    else:
        result = await session.execute(select(User).where(User.id == user_id))
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="User not found")

    # --------------------------
    #  Resolve book
    # --------------------------
    result = await session.execute(select(Book).where(Book.id == payload.book_id))
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # --------------------------
    #  Check availability
    # --------------------------
    available = (book.total_copies or 0) - (book.reserved_count or 0)
    if available <= 0:
        raise HTTPException(status_code=409, detail="No copies available")

    # --------------------------
    #  Create reservation
    # --------------------------
    reservation = Reservation(
        id=uuid4(),
        user_id=user_id,
        book_id=payload.book_id,
        from_date=date.today(),
        until=payload.until,
    )

    session.add(reservation)

    # update reserved_count and persist
    # ensure reserved_count isn't None
    if book.reserved_count is None:
        book.reserved_count = 0
    book.reserved_count += 1

    await session.commit()
    await session.refresh(reservation)

    return reservation

@router.get("/", response_model=list[ReservationOut])
async def get_reservations(
        user_email: str | None = Depends(get_user_email),
        session: AsyncSession = Depends(get_async_session)
):
    if not user_email:
        raise HTTPException(status_code=400, detail="X-User-Email header required")

    result = await session.execute(
        select(User).where(User.email == user_email)
    )
    user = result.scalar_one_or_none()

    if not user:
        return []

    result = await session.execute(
        select(Reservation).where(Reservation.user_id == user.id)
    )
    return result.scalars().all()


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
        raise HTTPException(status_code=404, detail="Reservation not found")

    # return copy
    result = await session.execute(select(Book).where(Book.id == reservation.book_id))
    book = result.scalar_one_or_none()

    if book and (book.reserved_count or 0) > 0:
        book.reserved_count -= 1

    await session.delete(reservation)
    await session.commit()

    return Response(status_code=204)
