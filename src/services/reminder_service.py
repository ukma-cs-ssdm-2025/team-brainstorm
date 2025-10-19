from datetime import date, timedelta
from src.core.database import RESERVATIONS, BOOKS, USERS

def get_due_soon_reservations(days_before=2):
    """Повертає список броней, у яких скоро закінчується термін."""
    today = date.today()
    due_soon = []
    for res in RESERVATIONS.values():
        if res["until"] and (res["until"] - today).days <= days_before:
            book = BOOKS.get(res["book_id"])
            user = USERS.get(res["user_id"])
            due_soon.append({
                "reservation_id": str(res["id"]),
                "book_title": book["title"] if book else "Unknown",
                "user_email": user["email"] if user else "Unknown",
                "days_left": (res["until"] - today).days
            })
    return due_soon


def send_reminders():
    """Імітація відправлення листів користувачам."""
    reminders = get_due_soon_reservations()
    for r in reminders:
        print(f"[Reminder] {r['user_email']}, поверніть книгу '{r['book_title']}' "
              f"через {r['days_left']} днів.")
    return reminders