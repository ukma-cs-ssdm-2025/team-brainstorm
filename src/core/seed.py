import asyncio
from src.core.database import async_session_maker
from src.core.security import hash_password
from src.api.models.bookdb import Book
from src.api.models.user import User, UserRole

async def seed():
    async with async_session_maker() as session:
        # додати книги
        book1 = Book(
            title="The Pragmatic Programmer",
            author="Andrew Hunt, David Thomas",
            isbn="978-0201616224",
            genres=["programming", "software"],
            total_copies=5
        )

        book2 = Book(
            title="Clean Code",
            author="Robert C. Martin",
            isbn="978-0132350884",
            genres=["programming"],
            total_copies=3
        )
        book3 = Book(
            title="дота 2 для чайників",
            author="шадоурейз",
            isbn="978-0132353254532",
            genres=["si-fi"],
            total_copies=100000
        )

        # додати користувача
        admin = User(
            email="admin@lib.com",
            password_hash=hash_password("admin123"),
            role=UserRole.librarian,
        )

        session.add_all([book1, book2, book3, admin])
        await session.commit()

if __name__ == "__main__":
    asyncio.run(seed())
