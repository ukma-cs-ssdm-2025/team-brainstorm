from uuid import uuid4
from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.user import User, UserRole
from src.api.schemas.user import UserCreate


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_user(session: AsyncSession, user_data: UserCreate) -> User:
    """Реєстрація нового користувача в PostgreSQL."""

    # Перевіряємо чи існує email
    existing = await session.execute(
        select(User).where(User.email == user_data.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )

    user = User(
        id=uuid4(),
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=pwd_context.hash(user_data.password),
        role=UserRole(user_data.role.value)
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


async def authenticate_user(
        session: AsyncSession,
        email: str,
        password: str
) -> User:
    """Перевіряє email та пароль користувача."""

    result = await session.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    return user


async def get_user_by_id(session: AsyncSession, user_id) -> User:
    """Повертає користувача по id."""

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user
