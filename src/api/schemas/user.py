from pydantic import BaseModel, EmailStr
from uuid import UUID
from enum import Enum


class UserRole(str, Enum):
    user = "user"
    librarian = "librarian"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.user


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    role: UserRole


class UserAuth(BaseModel):
    email: EmailStr
    password: str
