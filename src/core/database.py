import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@db:5432/library"
)


engine = create_async_engine(
    DATABASE_URL,
    future=True,
    echo=False
)


async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


SessionLocal = async_session_maker

Base = declarative_base()


async def get_async_session():
    async with async_session_maker() as session:
        yield session
