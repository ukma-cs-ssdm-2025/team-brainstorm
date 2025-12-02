from uuid import UUID, uuid4
from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.user import User, UserRole
from src.api.schemas.user import UserCreate


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -----------------------------
#    HELPERS
# -----------------------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Повертає користувача за email або None."""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


# -----------------------------
#    MAIN FUNCTIONS
# -----------------------------
async def create_user(session: AsyncSession, user_data: UserCreate) -> User:
    """
    Створює нового користувача:
    - перевіряє унікальність email
    - хешує пароль
    - зберігає користувача у БД
    """

    existing = await get_user_by_email(session, user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    user = User(
        id=uuid4(),
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=hash_password(user_data.password),
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
    """
    Авторизація користувача:
    - перевіряє чи існує email
    - порівнює хеш пароля
    """

    user = await get_user_by_email(session, email)

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    return user


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User:
    """
    Повертає користувача по ID або піднімає 404.
    """

    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user
