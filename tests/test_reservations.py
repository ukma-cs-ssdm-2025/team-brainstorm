from fastapi.testclient import TestClient
from src.api.main import app
from uuid import uuid4

client = TestClient(app)


def test_health():
    """Перевіряє, що API живе і повертає статус 'ok'."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# --- 🧩 КНИГИ ---
def test_list_books():
    """Перевіряє, що список книг повертається успішно."""
    r = client.get("/books/")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if len(data) > 0:
        book = data[0]
        assert "id" in book
        assert "title" in book
        assert "author" in book


def test_list_books_available_only():
    """Перевіряє фільтрацію доступних книг."""
    r = client.get("/books/?available_only=true")
    assert r.status_code == 200
    books = r.json()
    for b in books:
        assert b["total_copies"] - b.get("reserved_count", 0) > 0


# --- 📚 ОНЛАЙН-КАТАЛОГ ---
def test_search_books_by_title():
    """Перевіряє пошук книг за назвою в онлайн-каталозі."""
    r = client.get("/catalog/search", params={"query": "Python"})
    assert r.status_code == 200
    books = r.json()
    assert isinstance(books, list)
    for book in books:
        assert "title" in book
        assert "Python" in book["title"] or "Python" in book["description"]


def test_catalog_pagination():
    """Перевіряє пагінацію онлайн-каталогу."""
    r = client.get("/catalog?page=1&limit=2")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) <= 2


# --- 👤 КОРИСТУВАЧІ ТА РОЛІ ---
def test_user_registration_and_roles():
    """Перевіряє реєстрацію користувачів і ролі."""
    user_payload = {
        "username": f"user_{uuid4().hex[:6]}",
        "password": "test123",
        "role": "user"
    }
    librarian_payload = {
        "username": f"librarian_{uuid4().hex[:6]}",
        "password": "secure123",
        "role": "librarian"
    }

    # створення звичайного користувача
    r1 = client.post("/users/register", json=user_payload)
    assert r1.status_code == 201, r1.text
    data1 = r1.json()
    assert data1["role"] == "user"

    # створення бібліотекаря
    r2 = client.post("/users/register", json=librarian_payload)
    assert r2.status_code == 201
    data2 = r2.json()
    assert data2["role"] == "librarian"

    # бібліотекар має бачити всі резервації
    r3 = client.get("/reservations/all?role=librarian")
    assert r3.status_code == 200


# --- 🔔 НАГАДУВАННЯ ПРО ПОВЕРНЕННЯ ---
def test_send_reminder_for_due_books():
    """Перевіряє нагадування про повернення книг."""
    r = client.post("/reminders/send")
    assert r.status_code in (200, 202)
    result = r.json()
    assert "sent_reminders" in result
    assert isinstance(result["sent_reminders"], int)


# --- 📖 РЕЗЕРВАЦІЇ ---
def test_create_and_cancel_reservation():
    """Інтеграційний тест для створення і видалення резервації."""
    # Отримати одну книгу
    r = client.get("/books/")
    assert r.status_code == 200
    books = r.json()
    assert len(books) > 0, "Не знайдено жодної книги для тесту"

    book = books[0]
    user_id = str(uuid4())
    payload = {"user_id": user_id, "book_id": book["id"]}

    # Створити резервацію
    r2 = client.post("/reservations/", json=payload)
    assert r2.status_code == 201, r2.text
    res = r2.json()
    assert "id" in res
    assert res["user_id"] == user_id

    res_id = res["id"]

    # Скасувати резервацію
    r3 = client.delete(f"/reservations/{res_id}")
    assert r3.status_code == 204


def test_cancel_nonexistent_reservation():
    """Перевіряє, що скасування неіснуючої резервації повертає 404."""
    fake_id = str(uuid4())
    r = client.delete(f"/reservations/{fake_id}")
    assert r.status_code == 404


def test_create_reservation_with_invalid_book():
    """Перевіряє, що створення резервації з неіснуючою книгою не допускається."""
    user_id = str(uuid4())
    fake_book_id = str(uuid4())
    payload = {"user_id": user_id, "book_id": fake_book_id}

    r = client.post("/reservations/", json=payload)
    assert r.status_code == 404


def test_create_reservation_missing_fields():
    """Перевіряє валідацію при відсутніх полях."""
    r = client.post("/reservations/", json={"user_id": str(uuid4())})
    assert r.status_code == 422
