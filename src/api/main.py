from fastapi import FastAPI
from src.api.routes import books, reservations


app = FastAPI(
    title="Library Management API",
    version="0.1.0",
    description="Minimal Working Version for Lab 6"
)


# підключаємо маршрути
app.include_router(books.router, prefix="/books", tags=["books"])
app.include_router(reservations.router, prefix="/reservations", tags=["reservations"])


# простий health endpoint
@app.get("/health")
def health():
    return {"status": "ok"}

from src.api.routes import users, reminders

app.include_router(users.router)
app.include_router(reminders.router)

from src.api.routes import reviews

app.include_router(reviews.router)