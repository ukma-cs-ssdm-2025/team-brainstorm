import pytest
import sys
import os
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import date, timedelta

# додати src у шлях (щоб pytest бачив модулі)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.security import validate_password
from src.api.main import app
from src.core import database


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_db():
    """Очищає 'базу даних' перед кожним тестом і додає тестову книгу."""
    database.BOOKS.clear()
    database.RESERVATIONS.clear()
    database.USERS.clear()
    database.REVIEWS.clear()

    book_id = uuid4()
    database.BOOKS[book_id] = {
        "id": book_id,
        "isbn": "9783161484100",
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "total_copies": 2,
        "reserved_count": 0,
        "genres": ["programming"],
    }
    return book_id


# 1️⃣ Health check
def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# 2️⃣ Отримання списку книг
def test_list_books(clear_db):
    resp = client.get("/books/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Clean Architecture"


# 3️⃣ Оновлення книги бібліотекарем
def test_update_book_as_librarian(clear_db):
    book_id = next(iter(database.BOOKS))
    resp = client.patch(
        f"/books/{book_id}",
        headers={"X-Role": "librarian"},
        json={"title": "Updated Book"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Book"


# 4️⃣ Заборонене оновлення користувачем
def test_update_book_as_user_forbidden(clear_db):
    book_id = next(iter(database.BOOKS))
    resp = client.patch(
        f"/books/{book_id}",
        headers={"X-Role": "user"},
        json={"title": "Hack Try"},
    )
    assert resp.status_code == 403


# 5️⃣ Реєстрація та логін користувача
def test_user_register_and_login():
    resp = client.post("/users/register", json={
        "email": "test@example.com",
        "password": "123456",
        "role": "user"
    })
    assert resp.status_code == 200

    resp2 = client.post("/users/login", json={
        "email": "test@example.com",
        "password": "123456"
    })
    assert resp2.status_code == 200
    data = resp2.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


# 6️⃣ Створення резервації
def test_create_reservation(clear_db):
    user_id = uuid4()
    book_id = next(iter(database.BOOKS))
    database.USERS[user_id] = {"id": user_id, "email": "user@test.com"}

    payload = {"user_id": str(user_id), "book_id": str(book_id)}
    resp = client.post("/reservations/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["book_id"] == str(book_id)
    assert "from_date" in data


# 7️⃣ Скасування резервації
def test_cancel_reservation(clear_db):
    user_id = uuid4()
    book_id = next(iter(database.BOOKS))
    database.USERS[user_id] = {"id": user_id, "email": "cancel@test.com"}

    payload = {"user_id": str(user_id), "book_id": str(book_id)}
    res = client.post("/reservations/", json=payload).json()
    res_id = res["id"]

    resp = client.delete(f"/reservations/{res_id}")
    assert resp.status_code == 204
    assert res_id not in database.RESERVATIONS


# 8️⃣ Додавання і перегляд відгуків
def test_add_and_list_reviews(clear_db):
    user_id = uuid4()
    book_id = next(iter(database.BOOKS))
    database.USERS[user_id] = {"id": user_id, "email": "review@test.com"}

    resp = client.post(f"/books/{book_id}/reviews", json={
        "user_id": str(user_id),
        "rating": 5,
        "comment": "Excellent!"
    })
    assert resp.status_code == 201
    review_id = resp.json()["id"]

    resp2 = client.get(f"/books/{book_id}/reviews")
    data = resp2.json()
    assert data["count"] == 1
    assert data["average_rating"] == 5
    assert data["items"][0]["comment"] == "Excellent!"
    assert data["items"][0]["id"] == review_id


# 9️⃣ Видалення відгуку
def test_delete_review(clear_db):
    user_id = uuid4()
    book_id = next(iter(database.BOOKS))
    database.USERS[user_id] = {"id": user_id, "email": "delreview@test.com"}

    resp = client.post(f"/books/{book_id}/reviews", json={
        "user_id": str(user_id),
        "rating": 4,
        "comment": "Good"
    })
    review_id = resp.json()["id"]

    del_resp = client.delete(f"/books/reviews/{review_id}")
    assert del_resp.status_code == 204
    assert review_id not in database.REVIEWS


# 🔟 Перевірка нагадувань
def test_reminders(clear_db):
    user_id = uuid4()
    book_id = next(iter(database.BOOKS))
    database.USERS[user_id] = {"id": user_id, "email": "remind@test.com"}

    res_id = uuid4()
    database.RESERVATIONS[res_id] = {
        "id": res_id,
        "book_id": book_id,
        "user_id": user_id,
        "from_date": date.today(),
        "until": date.today() + timedelta(days=1)
    }

    resp = client.get("/reminders/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert "days_left" in data[0]
    assert data[0]["book_title"] == "Clean Architecture"

def test_list_books_filter_by_single_genre_returns_only_matching(clear_db):
    # act
    resp = client.get("/books/", params={"genres": "programming"})
    assert resp.status_code == 200
    data = resp.json()

    # assert: лише книги з жанром "programming"
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == "Clean Architecture"
    assert "programming" in data[0].get("genres", [])

def test_list_books_filter_by_unknown_genre_returns_empty(clear_db):
    resp = client.get("/books/", params={"genres": "history"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_available_books_count():
    response = client.get("/books/available_count")
    assert response.status_code == 200
    data = response.json()
    assert "available_count" in data
    assert isinstance(data["available_count"], int)

def test_get_book_by_id_not_found(clear_db):
    from uuid import uuid4
    missing_id = uuid4()
    resp = client.get(f"/books/{missing_id}")
    assert resp.status_code == 404

    # 1️⃣1️⃣ Перевірка паролю

def test_password_too_short_raises():
        with pytest.raises(ValueError) as e:
            validate_password("short")
        assert "at least 8" in str(e.value).lower()

def test_password_valid_length_passes():
        # рівно 8 символів
        validate_password("abc12345")


