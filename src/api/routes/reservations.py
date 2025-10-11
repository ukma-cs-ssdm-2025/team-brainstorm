from fastapi import APIRouter, HTTPException, status, Response
from pydantic import BaseModel
from uuid import UUID
from datetime import date
from src.core.database import BOOKS, RESERVATIONS, DB_LOCK
from src.services.reservations_service import create_reservation_for_user


router = APIRouter()


class ReservationCreate(BaseModel):
    user_id: UUID
    book_id: UUID
    until: date | None = None


class ReservationOut(BaseModel):
    id: UUID
    user_id: UUID
    book_id: UUID
    from_date: date
    until: date | None = None


@router.post("/", response_model=ReservationOut, status_code=status.HTTP_201_CREATED)
def create_reservation(payload: ReservationCreate):
    res = create_reservation_for_user(payload.user_id, payload.book_id, payload.until)
    if isinstance(res, HTTPException):
        raise res
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
