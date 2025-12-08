import asyncio
from sqlalchemy import select
from src.core.database import async_session_maker
from src.core.security import hash_password
from src.api.models.bookdb import Book
from src.api.models.user import User, UserRole


async def seed():


    async with async_session_maker() as session:

        # ---------------------------
        # 1. Seed books
        # ---------------------------
        books_to_seed = [
            {
                "title": "The Pragmatic Programmer",
                "author": "Andrew Hunt, David Thomas",
                "isbn": "978-0201616224",
                "genres": ["programming", "software"],
                "total_copies": 5,
                "cover_image": "/static/covers/pragmatic.jpg",
            },
            {
                "title": "Clean Code",
                "author": "Robert C. Martin",
                "isbn": "978-0132350884",
                "genres": ["programming"],
                "total_copies": 3,
                "cover_image": "/static/covers/clean.png",
            },
            {
                "title": "Дота 2 для чайників",
                "author": "Шадоу Рейз",
                "isbn": "978-0132353254532",
                "genres": ["sci-fi", "gaming"],
                "total_copies": 100000,
                "cover_image": "/static/covers/dota2.png",
            },
        ]

        for data in books_to_seed:
            stmt = select(Book).where(Book.isbn == data["isbn"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                book = Book(
                    title=data["title"],
                    author=data["author"],
                    isbn=data["isbn"],
                    genres=data["genres"],
                    total_copies=data["total_copies"],
                    reserved_count=0,        # важливо!
                    cover_image=data.get("cover_image"),
                )
                session.add(book)
                print(f"[ADDED] Book: {book.title}")
            else:
                cover = data.get("cover_image")
                if cover:
                    existing.cover_image = cover
                print(f"[SKIP] Book already exists: {existing.title}")

        # ---------------------------
        # 2. Seed admin user
        # ---------------------------
        stmt = select(User).where(User.email == "admin@lib.com")
        result = await session.execute(stmt)
        admin = result.scalar_one_or_none()

        if not admin:
            admin = User(
                email="admin@lib.com",
                password_hash=hash_password("admin123"),
                role=UserRole.librarian,
            )
            session.add(admin)
            print("[ADDED] Admin user created")
        else:
            print("[SKIP] Admin already exists")

        await session.commit()
        print("✨ SEED COMPLETE")


if __name__ == "__main__":
    asyncio.run(seed())
