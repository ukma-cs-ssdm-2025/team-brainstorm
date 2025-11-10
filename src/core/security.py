import os
from secrets import token_urlsafe
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt

# 🔐 Безпечне керування секретом
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = token_urlsafe(32)
    print("[WARN] Використовується тимчасовий SECRET_KEY (режим розробки)")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# 🔑 Контекст для хешування паролів
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Хешує пароль користувача (bcrypt приймає максимум 72 байти)."""
    password = password.encode("utf-8")[:72].decode("utf-8", "ignore")
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Перевіряє відповідність введеного пароля хешу."""
    plain = plain.encode("utf-8")[:72].decode("utf-8", "ignore")
    return pwd_context.verify(plain, hashed)


def create_token(data: dict) -> str:
    """Створює JWT-токен із часом життя ACCESS_TOKEN_EXPIRE_MINUTES."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
        raise ValueError("Пароль має бути рядком")

    pwd = password.strip()

    if not pwd:
        raise ValueError("Пароль не може бути порожнім або складатися лише з пробілів")

    if len(pwd) < 8:
        raise ValueError("Пароль має містити щонайменше 8 символів")

    has_letter = any(ch.isalpha() for ch in pwd)
    has_digit = any(ch.isdigit() for ch in pwd)

    if not has_letter:
        raise ValueError("Пароль має містити хоча б одну літеру")

    if not has_digit:
        raise ValueError("Пароль має містити хоча б одну цифру")
