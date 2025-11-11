from fastapi import APIRouter, HTTPException, status, Response, Depends, Header
from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import date
from src.core.database import BOOKS, RESERVATIONS, DB_LOCK, USERS
from src.services.reservations_service import create_reservation_for_user


router = APIRouter()


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


def get_current_user_email(x_user_email: str | None = Header(None, alias="X-User-Email")) -> str | None:
    if x_user_email is None:
        return None
    email = x_user_email.strip().lower()
    return email or None


@router.post("/", response_model=ReservationOut, status_code=status.HTTP_201_CREATED)
def create_reservation(payload: ReservationCreate, user_email: str | None = Depends(get_current_user_email)):
    user_id: UUID | None = payload.user_id

    if user_id is None:
        if not user_email:
            raise HTTPException(status_code=400, detail="Provide user_id or X-User-Email header")
        # зарезоливити юзера по емейлу та створення мінімального запису
        with DB_LOCK:
            for uid, u in USERS.items():
                if str(u.get("email", "")).strip().lower() == user_email:
                    user_id = uid
                    break
            if user_id is None:
                uid = uuid4()
                USERS[uid] = {"id": uid, "email": user_email}
                user_id = uid
    else:
        # впевнитись шо є такий юзер
        with DB_LOCK:
            if user_id not in USERS:
                raise HTTPException(status_code=404, detail="User not found")

    res = create_reservation_for_user(user_id, payload.book_id, payload.until)
    return ReservationOut(**res)


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_reservation(reservation_id: UUID):
    with DB_LOCK:
        res = RESERVATIONS.get(reservation_id)
        if not res:
            raise HTTPException(status_code=404, detail="Reservation not found")
        book = BOOKS.get(res["book_id"])
        if book:
            book["reserved_count"] = max(0, book.get("reserved_count", 1) - 1)
        del RESERVATIONS[reservation_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)
