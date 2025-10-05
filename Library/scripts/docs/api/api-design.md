# API Design Documentation — Library Management API

## 1. Overview
**Project name:** Library Management API  
**Purpose:** RESTful API для управління бібліотекою — користувачі можуть переглядати книги, бронювати, скасовувати бронювання та шукати доступні екземпляри.  
**Approach:** Code-First (FastAPI автоматично генерує OpenAPI документацію).

---

## 2. Resources & Endpoints

### 📘 Books
| Method | Endpoint | Description | Request | Response | Status |
|--------|-----------|--------------|----------|-----------|--------|
| **GET** | `/books` | Отримати список усіх книг. Можна фільтрувати лише доступні. | Query: `available_only: bool` | `[Book]` | 200 |
| **GET** | `/books/availability` | Пошук доступних книг за назвою. | Query: `title: str (optional)` | `[Book]` | 200 |

### 📗 Reservations
| Method | Endpoint | Description | Request | Response | Status |
|--------|-----------|-------------|----------|-----------|--------|
| **POST** | `/reservations` | Створити нове бронювання книги. | `ReservationCreate` (user_id, book_id, until) | `Reservation` | 201 |
| **DELETE** | `/reservations/{reservation_id}` | Скасувати існуюче бронювання. | Path: `reservation_id: UUID` | None | 204 |
| **GET** | `/users/{user_id}/reservations` | Переглянути всі бронювання певного користувача. | Path: `user_id: UUID` | `[Reservation]` | 200 |

---

## 3. Data Models

### `Book`
| Field | Type | Example | Description |
|--------|------|----------|-------------|
| id | UUID | `3fa85f64-5717-4562-b3fc-2c963f66afa6` | Унікальний ідентифікатор книги |
| isbn | str | `978-3-16-148410-0` | ISBN код книги |
| title | str | `Clean Code` | Назва книги |
| author | str | `Robert C. Martin` | Автор книги |
| total_copies | int | `3` | Загальна кількість екземплярів |

### `Reservation`
| Field | Type | Example | Description |
|--------|------|----------|-------------|
| id | UUID | — | Ідентифікатор бронювання |
| user_id | UUID | — | Користувач, який зробив бронювання |
| book_id | UUID | — | Заброньована книга |
| from_date | date | `2025-10-05` | Дата початку бронювання |
| until | date/null | `2025-10-10` | Дата завершення бронювання |

---

## 4. Design Decisions
- Використано **FastAPI**, оскільки він нативно підтримує автогенерацію OpenAPI.
- Код побудовано за принципом **Code-First**, документація формується з анотацій.
- Валідація даних виконується через **Pydantic models**.
- Використано **UUID** для унікальної ідентифікації ресурсів.
- Mock data використовується замість бази даних (для демонстрації функцій).
- Логіка роботи з книгами і резерваціями ізольована у пам’яті (`BOOKS`, `RESERVATIONS`).

---

## 5. HTTP Status Codes
| Code | Meaning | Використання |
|------|----------|--------------|
| 200 | OK | Успішна відповідь |
| 201 | Created | Ресурс створено (бронювання) |
| 204 | No Content | Ресурс успішно видалено |
| 404 | Not Found | Книга або бронювання не знайдені |
| 409 | Conflict | Книга недоступна для бронювання |
| 422 | Validation Error | Невірні параметри запиту |

---

## 6. Example Workflow
1. Користувач отримує список книг (`GET /books`)
2. Обирає книгу й бронює її (`POST /reservations`)
3. Переглядає свої бронювання (`GET /users/{user_id}/reservations`)
4. Може скасувати бронювання (`DELETE /reservations/{reservation_id}`)
5. Може шукати книги по назві (`GET /books/availability`)

---

## 7. Future Improvements
- Додати аутентифікацію користувачів.
- Додати збереження у базу дани.
- Додати пагінацію і фільтри для `/books`.
- Інтегрувати CI/CD для автогенерації документації при push.
