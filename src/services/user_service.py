from uuid import uuid4
from fastapi import HTTPException, status
from passlib.context import CryptContext
from src.core.database import USERS, DB_LOCK
from src.api.schemas.user import UserCreate, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_user(user_data: UserCreate):
    """Реєструє нового користувача."""
    with DB_LOCK:
        if any(u["email"] == user_data.email for u in USERS.values()):
            raise HTTPException(status_code=400, detail="User already exists")

        user_id = uuid4()
        user = {
            "id": user_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "hashed_password": pwd_context.hash(user_data.password),
            "role": user_data.role,
        }
        USERS[user_id] = user
        return user


def authenticate_user(email: str, password: str):
    """Перевіряє email і пароль користувача."""
    for u in USERS.values():
        if u["email"] == email and pwd_context.verify(password, u["hashed_password"]):
            return u
    raise HTTPException(status_code=401, detail="Invalid credentials")


def get_user_by_id(user_id):
    user = USERS.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
