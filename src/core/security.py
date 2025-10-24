from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "super_secret_key"
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def validate_password(password: str) -> None:
    """
    Перевіряє, що пароль не порожній і має щонайменше 8 символів.
    """
    if password is None:
        raise ValueError("Password cannot be None")
    pwd = password.strip()
    if not pwd:
        raise ValueError("Password cannot be empty or whitespace")
    if len(pwd) < 8:
        raise ValueError("Password must be at least 8 characters long")
