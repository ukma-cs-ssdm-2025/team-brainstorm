from fastapi.testclient import TestClient
from src.api.main import app
from uuid import uuid4

client = TestClient(app)


def test_health():
    """Перевіряє, що API живе і повертає статус 'ok'."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_list_books():
    """Перевіряє, що список книг повертається успішно."""
    r = client.get("/books/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


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
    assert r2.status_code == 201
    res = r2.json()
    res_id = res["id"]

    # Видалити резервацію
    r3 = client.delete(f"/reservations/{res_id}")
    assert r3.status_code == 204
