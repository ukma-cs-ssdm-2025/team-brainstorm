from fastapi import APIRouter
from datetime import date, timedelta
from src.core.database import RESERVATIONS, BOOKS

router = APIRouter(prefix="/reminders", tags=["Reminders"])

@router.get("/")
def get_reminders():
    today = date.today()
    reminders = []
    for res in RESERVATIONS.values():
        if res.get("until") and (res["until"] - today).days <= 2:
            book = BOOKS.get(res["book_id"])
            reminders.append({
                "reservation_id": res["id"],
                "book_title": book["title"],
                "days_left": (res["until"] - today).days
            })
    return reminders
