from fastapi import FastAPI
from src.api.routes import books, reservations, users, reminders, reviews
from src.core.database import Base, engine



app = FastAPI(
    title="Library Management API",
    version="0.1.0",
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("📌 DATABASE: all tables created")

# маршрути
app.include_router(books.router, prefix="/api/books")
app.include_router(users.router, prefix="/api")
app.include_router(users.router, prefix="/api/users")
app.include_router(reservations.router, prefix="/api/reservations")
app.include_router(reviews.router, prefix="/api/reviews")
app.include_router(reminders.router, prefix="/api/reminders")

@app.get("/api/health")
def health():
    return {"status": "ok"}
