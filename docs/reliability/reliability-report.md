# 🛡️ Звіт про виправлення вразливостей та підвищення надійності — Library API

## 🔐 1. Жорстко заданий SECRET_KEY (SEC01)

**Ризик:** Високий  
**Файл:** `src/core/security.py`

Fault: Я зашив секрет у вихідний код.
Error: Система завжди використовувала один і той самий ключ незалежно від середовища.
Failure: Потенційний витік токенів і несанкціонований доступ до API.
Severity: 🔴 Високий

### ❌ Вразливий код
```python
SECRET_KEY = "super_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
```

### ✅ Виправлений код 
```python
import os
from secrets import token_urlsafe

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = token_urlsafe(32)
    print("[WARN] Використовується тимчасовий SECRET_KEY (режим розробки)")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
```
> Секретний ключ перенесено у змінні середовища; тимчасовий ключ дозволено лише для розробки.

Федін Володимир
---


## 🧮 2. Некоректний підрахунок доступних книг (BUG01)

**Ризик:** Середній  
**Файл:** `src/api/routes/books.py`

Fault: Помилкове використання неіснуючого або застарілого поля reserved.
Error: Обчислення доступних книг давало некоректний результат (наприклад, 0 при наявності вільних примірників).
Failure: Користувач бачив помилкову інформацію — книги могли здаватися недоступними.
Severity: 🟡 Середній

### ❌ Вразливий код
```python
if book["total_copies"] - book.get("reserved", 0) > 0:
```

### ✅ Виправлений код
```python
if book["total_copies"] - book.get("reserved_count", 0) > 0:
```

> Використано правильне поле `reserved_count` замість застарілого `reserved`.

Федін Володимир
---




## 🧩 Підсумкова таблиця

| Код | Вразливість | Ризик | Статус |
|------|----------------|------|---------|
| SEC01 | Жорстко заданий SECRET_KEY | 🔴 Високий | ✅ Виправлено |
| BUG01 | reserved → reserved_count | 🟡 Середній | ✅ Виправлено |


---


# 3. Коректна ідентифікація користувача при резервації (BUG02) Ковтонюк Анастасія

Ризик: Середній  
Файли: `src/api/routes/reservations.py`, `src/services/reservations_service.py`, `frontend/app.js`

Fault: Фронтенд генерував випадковий `user_id` для резервацій, а бекенд приймав будь-який UUID без перевірки існування користувача.  
Error: Створювались резервації, не повʼязані з реальним користувачем (сирітські записи).  
Failure: Нагадування та інший функціонал не мали доступу до email користувача, що унеможливлювало коректні повідомлення та аудит.

---

## Код з помилкою

Backend (до):
```py
# src/api/routes/reservations.py
class ReservationCreate(BaseModel):
    user_id: UUID
    book_id: UUID
    until: date | None = None

@router.post("/", response_model=ReservationOut, status_code=status.HTTP_201_CREATED)
def create_reservation(payload: ReservationCreate):
    res = create_reservation_for_user(payload.user_id, payload.book_id, payload.until)
    if isinstance(res, HTTPException):
        raise res
    return ReservationOut(**res)
```

```py
# src/services/reservations_service.py
with DB_LOCK:
    book = BOOKS.get(book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    # ... створення резервації без перевірки існування користувача
```

Frontend (до):
```js
// frontend/app.js
const user_id = crypto.randomUUID();
const payload = { user_id, book_id: b.id, until: untilStr };
await fetch(`${apiBase()}/reservations/`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload),
});
```

---

## Виправлений код

Backend (після):
```py
# src/api/routes/reservations.py
from fastapi import Depends, Header
from uuid import uuid4, UUID
from src.core.database import USERS, DB_LOCK

class ReservationCreate(BaseModel):
    user_id: UUID | None = None
    book_id: UUID
    until: date | None = None

def get_current_user_email(x_user_email: str | None = Header(None, alias="X-User-Email")) -> str | None:
    if x_user_email is None:
        return None
    email = x_user_email.strip().lower()
    return email or None

@router.post("/", response_model=ReservationOut, status_code=status.HTTP_201_CREATED)
def create_reservation(payload: ReservationCreate, user_email: str | None = Depends(get_current_user_email)):
    user_id: UUID | None = payload.user_id

    if user_id is None:
        if not user_email:
            raise HTTPException(status_code=400, detail="Provide user_id or X-User-Email header")
        with DB_LOCK:
            for uid, u in USERS.items():
                if str(u.get("email", "")).strip().lower() == user_email:
                    user_id = uid
                    break
            if user_id is None:
                uid = uuid4()
                USERS[uid] = {"id": uid, "email": user_email}
                user_id = uid
    else:
        with DB_LOCK:
            if user_id not in USERS:
                raise HTTPException(status_code=404, detail="User not found")

    res = create_reservation_for_user(user_id, payload.book_id, payload.until)
    return ReservationOut(**res)
```

```py
# src/services/reservations_service.py
from src.core.database import USERS

with DB_LOCK:
    if user_id not in USERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    book = BOOKS.get(book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    # ... створення резервації
```

Frontend (після):
```js
// frontend/app.js
const email = userEmail();
if (!email) {
  showToast("Вкажіть email (X-User-Email)", "danger");
  return;
}
const payload = { book_id: b.id, until: untilStr };
await fetch(`${apiBase()}/reservations/`, {
  method: "POST",
  headers: { "Content-Type": "application/json", "X-User-Email": email },
  body: JSON.stringify(payload),
});
```

> Тепер бекенд сам резолвить `user_id` за email або вимагає валідний наявний `user_id`. Створення “сирітських” резервацій заблоковано.

---

### Що саме змінилось
- Фронтенд перестав генерувати випадковий `user_id`; надсилає `X-User-Email` у заголовку.
- Бекенд резолвить користувача за email.
- Додано перевірку існування користувача у сервісі перед створенням резервації.

---

## Підсумкова таблиця

| Код   | Вразливість                                                        | Ризик   | Статус     |
|------:|--------------------------------------------------------------------|---------|------------|
| BUG02 | Резервація без верифікованого користувача (random UUID, no check) | Середній| Виправлено |

Ось 2 проблеми у стилі твоїх колег, які ти можеш просто додати в кінець файлу:

---

## 📖 4. Відсутність обробки помилок при доступі до файлу e-book (RELIABILITY01)

**Ризик:** Середній  
**Файл:** `src/api/routes/books.py`

**Fault:** Відсутня обробка IOError/PermissionError при читанні файлу електронної книги.  
**Error:** FileResponse намагається прочитати недоступний або пошкоджений файл без перевірки.  
**Failure:** Сервер повертає 500 Internal Server Error замість зрозумілої помилки користувачу.  
**Severity:** 🟡 Середній

### ❌ Вразливий код
```python
@router.get("/{book_id}/ebook", response_class=FileResponse)
def get_ebook(book_id: UUID):
    with DB_LOCK:
        book = BOOKS.get(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        ebook_path = book.get("ebook_url")
        if not ebook_path:
            raise HTTPException(status_code=404, detail="E-book version not available")

        project_root = Path(__file__).resolve().parents[2]
        abs_path = (project_root / ebook_path).resolve()

    if not abs_path.exists():
        raise HTTPException(status_code=404, detail=f"E-book file not found: {abs_path}")

    # ❌ Немає обробки помилок читання файлу
    return FileResponse(
        abs_path,
        media_type="application/pdf",
        filename=f"{book['title'].replace(' ', '_')}.pdf"
    )
```

### ✅ Рекомендоване виправлення
```python
import logging

logger = logging.getLogger(__name__)

@router.get("/{book_id}/ebook", response_class=FileResponse)
def get_ebook(book_id: UUID):
    with DB_LOCK:
        book = BOOKS.get(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        ebook_path = book.get("ebook_url")
        if not ebook_path:
            raise HTTPException(status_code=404, detail="E-book version not available")

        project_root = Path(__file__).resolve().parents[2]
        abs_path = (project_root / ebook_path).resolve()

    if not abs_path.exists():
        logger.error(f"E-book file not found: {abs_path} for book {book_id}")
        raise HTTPException(status_code=404, detail="E-book file not found")
    
    if not abs_path.is_file():
        logger.error(f"E-book path is not a file: {abs_path}")
        raise HTTPException(status_code=500, detail="Invalid e-book path")
    
    try:
        with open(abs_path, 'rb') as f:
            f.read(1)
    except PermissionError:
        logger.error(f"Permission denied for e-book: {abs_path}")
        raise HTTPException(status_code=500, detail="E-book access denied")
    except IOError as e:
        logger.error(f"IOError reading e-book {abs_path}: {e}")
        raise HTTPException(status_code=500, detail="E-book file is corrupted")

    return FileResponse(
        abs_path,
        media_type="application/pdf",
        filename=f"{book['title'].replace(' ', '_')}.pdf"
    )
```

> Додано перевірку прав доступу, обробку IOError та логування помилок для відстеження проблем з файловою системою.

**Зінченко Вероніка**

---

## 🔒 5. Відсутність таймауту на операції з DB_LOCK (RELIABILITY06)

**Ризик:** Високий  
**Файли:** `src/services/reservations_service.py`, `src/services/reviews_service.py`, `src/services/user_service.py`

**Fault:** Використання `Lock()` без timeout при операціях з БД.  
**Error:** Deadlock або нескінченне очікування при конкурентному доступі.  
**Failure:** API перестає відповідати, всі запити "висять", система недоступна.  
**Severity:** 🔴 Високий

### ❌ Вразливий код

```python
# src/services/reservations_service.py
def create_reservation_for_user(user_id, book_id, until_date=None):
    with DB_LOCK:  # ❌ Немає timeout
        if user_id not in USERS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        book = BOOKS.get(book_id)
        if not book:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
        # ... довгі операції
```

### ✅ Рекомендоване виправлення

```python
import logging
from threading import Lock

logger = logging.getLogger(__name__)

DB_LOCK = Lock()
LOCK_TIMEOUT = 5  # секунди

def create_reservation_for_user(user_id, book_id, until_date=None):
    if not DB_LOCK.acquire(timeout=LOCK_TIMEOUT):
        logger.error(f"Failed to acquire DB_LOCK for reservation (timeout={LOCK_TIMEOUT}s)")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable, please try again"
        )
    
    try:
        if user_id not in USERS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        book = BOOKS.get(book_id)
        if not book:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
        
        available = book["total_copies"] - book.get("reserved_count", 0)
        if available <= 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No copies available")

        res_id = uuid4()
        reservation = {
            "id": res_id,
            "user_id": user_id,
            "book_id": book_id,
            "from_date": date.today(),
            "until": until_date,
        }

        RESERVATIONS[res_id] = reservation
        book["reserved_count"] = book.get("reserved_count", 0) + 1

        return reservation
    finally:
        DB_LOCK.release()
```

> Додано timeout на захоплення локу, логування проблем та гарантоване звільнення ресурсу через try/finally.

**Зінченко Вероніка**

---

## Підсумкова таблиця

| Код   | Вразливість                                                        | Ризик   | Статус     |
|------:|--------------------------------------------------------------------|---------|------------|
| RELIABILITY01 | Відсутність обробки помилок при доступі до e-book файлу | Середній| 🔄 У процесі |
| RELIABILITY06 | Відсутність таймауту на операції з DB_LOCK (deadlock) | Високий | 🔄 У процесі |
