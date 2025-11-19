from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4

from src.core.security import hash_password, verify_password, create_token
from src.core.database import get_async_session
from src.api.models.user import User

router = APIRouter()


# ---------- Pydantic схеми ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str  # "user" або "librarian"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ---------- POST /register ----------
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, session: AsyncSession = Depends(get_async_session)):
    # Чи існує email?
    query = select(User).where(User.email == user.email)
    result = await session.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Створюємо нового юзера
    new_user = User(
        id=uuid4(),
        email=user.email,
        password_hash=hash_password(user.password),
        role=user.role
    )

    session.add(new_user)
    await session.commit()

    return {"msg": "Registered successfully"}


# ---------- POST /login ----------
@router.post("/login")
async def login(data: UserLogin, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.email == data.email)
    result = await session.execute(query)
    user: User | None = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({"sub": str(user.id), "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "role": user.role
    }
