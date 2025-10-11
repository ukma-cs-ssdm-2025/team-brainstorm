from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    LIBRARIAN = "librarian"


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., example="John Doe")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.USER


class UserOut(UserBase):
    id: UUID
    role: UserRole


class UserAuth(BaseModel):
    email: EmailStr
    password: str
