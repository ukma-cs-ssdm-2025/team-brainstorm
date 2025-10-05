from fastapi import FastAPI, HTTPException, Path, Query, status
from pydantic import BaseModel, Field, constr
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import date
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Library Management API",
    version="1.0.0",
    description="API для онлайн-каталогу бібліотеки"
)

# ---------- Models ----------
class Book(BaseModel):
    id: UUID
    isbn: constr(min_length=10, max_length=17) = Field(..., example="978-3-16-148410-0")
    title: str = Field(..., example="Clean Code")
    author: str = Field(..., example="Robert C. Martin")
    total_copies: int = Field(..., example=3, ge=0)

class ReservationCreate(BaseModel):
    user_id: UUID
    book_id: UUID
    until: Optional[date] = None

class Reservation(BaseModel):
    id: UUID
    user_id: UUID
    book_id: UUID
    from_date: date
    until: Optional[date]

# ---------- Mock DB ----------
BOOKS = {}
RESERVATIONS = {}

#тестова книга
book_id = uuid4()
BOOKS[book_id] = {
    "id": book_id,
    "isbn": "978-3-16-148410-0",
    "title": "Clean Code",
    "author": "Robert C. Martin",
    "total_copies": 3,
    "reserved_count": 0
}

# ---------- Endpoints ----------
@app.get("/books", response_model=List[Book], summary="Список книг")
def list_books(available_only: bool = Query(False)):
    results = []
    for b in BOOKS.values():
        if available_only and (b["total_copies"] - b.get("reserved_count", 0)) <= 0:
            continue
        results.append(Book(**b))
    return results

@app.post("/reservations", response_model=Reservation, status_code=status.HTTP_201_CREATED)
def create_reservation(payload: ReservationCreate):
    book = BOOKS.get(payload.book_id)
    if not book:
        raise HTTPException(404, "Book not found")
    if book["total_copies"] - book.get("reserved_count", 0) <= 0:
        raise HTTPException(409, "No copies available")

    res_id = uuid4()
    reservation = {
        "id": res_id,
        "user_id": payload.user_id,
        "book_id": payload.book_id,
        "from_date": date.today(),
        "until": payload.until
    }
    RESERVATIONS[res_id] = reservation
    book["reserved_count"] += 1
    return Reservation(**reservation)

@app.delete("/reservations/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_reservation(reservation_id: UUID = Path(...)):
    res = RESERVATIONS.get(reservation_id)
    if not res:
        raise HTTPException(404, "Reservation not found")
    book = BOOKS.get(res["book_id"])
    if book:
        book["reserved_count"] -= 1
    del RESERVATIONS[reservation_id]
    return JSONResponse(status_code=204, content=None)

@app.get("/users/{user_id}/reservations", response_model=List[Reservation])
def user_reservations(user_id: UUID):
    return [Reservation(**r) for r in RESERVATIONS.values() if r["user_id"] == user_id]

@app.get("/books/availability", response_model=List[Book])
def search_books(title: Optional[str] = None):
    return [
        Book(**b) for b in BOOKS.values()
        if (not title or title.lower() in b["title"].lower())
           and (b["total_copies"] - b.get("reserved_count", 0)) > 0
    ]
