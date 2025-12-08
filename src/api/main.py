from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api.routes import books, reservations, users, reminders, reviews
from src.api.routes.favorites import router as favorites_router
from src.core.database import Base, engine

app = FastAPI(
    title="Library Management API",
    version="0.1.0",
)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "frontend" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("📌 DATABASE: all tables created")


# ------------------------
# 🚀 Правильна реєстрація маршрутів
# ------------------------
app.include_router(users.router, prefix="/api/users")
app.include_router(books.router, prefix="/api/books")
app.include_router(reservations.router, prefix="/api/reservations")
app.include_router(reviews.router, prefix="/api")
app.include_router(reminders.router, prefix="/api/reminders")
app.include_router(favorites_router, prefix="/api/favorites")


@app.get("/api/health")
def health():
    return {"status": "ok"}
