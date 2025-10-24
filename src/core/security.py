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
    Перевіряє пароль користувача згідно вимоги NFR-005:
    - Мінімум 8 символів.
    - Не може бути порожнім або складатися лише з пробілів.
    - Має містити хоча б одну літеру та одну цифру.

    Raises:
        ValueError: якщо пароль не відповідає вимогам.
    """
    if not isinstance(password, str):
        raise ValueError("Password must be a string")

    pwd = password.strip()

    if not pwd:
        raise ValueError("Password cannot be empty or whitespace")

    if len(pwd) < 8:
        raise ValueError("Password must be at least 8 characters long")

    has_letter = any(ch.isalpha() for ch in pwd)
    has_digit = any(ch.isdigit() for ch in pwd)

    if not has_letter:
        raise ValueError("Password must include at least one letter")

    if not has_digit:
        raise ValueError("Password must include at least one number")
