from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from uuid import uuid4
from src.core.security import hash_password, verify_password, create_token

router = APIRouter(prefix="/users", tags=["Users"])

# Тимчасова база користувачів (у пам’яті)
USERS = {}

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str  # "user" або "librarian"

@router.post("/register")
def register(user: UserCreate):
    if user.email in USERS:
        raise HTTPException(status_code=400, detail="User already exists")
    USERS[user.email] = {
        "id": str(uuid4()),
        "email": user.email,
        "password": hash_password(user.password),
        "role": user.role
    }
    return {"msg": "Registered successfully"}

class UserLogin(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
def login(data: UserLogin):
    user = USERS.get(data.email)
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"sub": data.email, "role": user["role"]})
    return {"access_token": token, "token_type": "bearer"}
