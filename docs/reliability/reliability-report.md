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


