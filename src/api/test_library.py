import copy
from datetime import date, timedelta
from uuid import uuid4, UUID

import pytest
from fastapi.testclient import TestClient

import main



@pytest.fixture()
def client():
    return TestClient(main.app)


@pytest.fixture(autouse=True)
def reset_state():

    books_snapshot = copy.deepcopy(main.BOOKS)
    reservations_snapshot = copy.deepcopy(main.RESERVATIONS)

    main.RESERVATIONS.clear()
    for book in main.BOOKS.values():
        book["reserved_count"] = 0
    try:
        yield
    finally:
        main.BOOKS.clear()
        main.BOOKS.update(books_snapshot)
        main.RESERVATIONS.clear()
        main.RESERVATIONS.update(reservations_snapshot)



def reserve_one(client, *, user_id=None, book_id=None, until=None):
    payload = {
        "user_id": str(user_id or uuid4()),
        "book_id": str(book_id or main.book_id),
        "until": until,
    }
    return client.post("/reservations", json=payload)



def test_books_list_contains_seed_book_and_hides_internal_fields(client):
    resp = client.get("/books")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list) and len(data) >= 1


    book = next((b for b in data if b["id"] == str(main.book_id)), None)
    assert book is not None, "Seed book missing from /books"


    assert "reserved_count" not in book
    assert set(book.keys()) == {"id", "isbn", "title", "author", "total_copies"}


def test_books_available_only_filters_out_fully_reserved(client):

    main.BOOKS[main.book_id]["reserved_count"] = main.BOOKS[main.book_id]["total_copies"]
    resp = client.get("/books", params={"available_only": True})
    assert resp.status_code == 200
    data = resp.json()
    assert all(b["id"] != str(main.book_id) for b in data)



def test_create_reservation_201_and_increments_counter(client):
    before = main.BOOKS[main.book_id]["reserved_count"]
    uid = uuid4()

    resp = reserve_one(client, user_id=uid)
    assert resp.status_code == 201, resp.text
    body = resp.json()


    assert UUID(body["id"])
    assert body["user_id"] == str(uid)
    assert body["book_id"] == str(main.book_id)
    assert body["from_date"] == date.today().isoformat()
    assert body["until"] is None


    after = main.BOOKS[main.book_id]["reserved_count"]
    assert after == before + 1


def test_create_reservation_accepts_until_date_and_echoes_it(client):
    until = (date.today() + timedelta(days=7)).isoformat()
    resp = reserve_one(client, until=until)
    assert resp.status_code == 201
    assert resp.json()["until"] == until


def test_create_reservation_404_for_unknown_book(client):
    resp = reserve_one(client, book_id=uuid4())
    assert resp.status_code == 404
    assert "Book not found" in resp.text


def test_create_reservation_409_when_no_copies_left(client):

    book = main.BOOKS[main.book_id]
    book["reserved_count"] = book["total_copies"]
    resp = reserve_one(client)
    assert resp.status_code == 409
    assert "No copies available" in resp.text


def test_create_reservation_422_on_invalid_payload(client):

    resp = client.post("/reservations", json={})
    assert resp.status_code == 422



def test_cancel_reservation_204_decrements_counter_and_removes_it(client):
    create = reserve_one(client)
    assert create.status_code == 201
    res_id = create.json()["id"]
    before = main.BOOKS[main.book_id]["reserved_count"]

    resp = client.delete(f"/reservations/{res_id}")
    assert resp.status_code == 204

    after = main.BOOKS[main.book_id]["reserved_count"]
    assert after == before - 1
    assert UUID(res_id) not in main.RESERVATIONS


def test_cancel_reservation_404_if_not_found(client):
    resp = client.delete(f"/reservations/{uuid4()}")
    assert resp.status_code == 404
    assert "Reservation not found" in resp.text


def test_cancel_reservation_422_for_invalid_uuid(client):
    resp = client.delete("/reservations/not-a-uuid")
    assert resp.status_code == 422



def test_user_reservations_returns_only_for_that_user(client):
    user_a = uuid4()
    user_b = uuid4()

    r1 = reserve_one(client, user_id=user_a)
    r2 = reserve_one(client, user_id=user_a)
    r3 = reserve_one(client, user_id=user_b)
    assert r1.status_code == r2.status_code == r3.status_code == 201

    resp = client.get(f"/users/{user_a}/reservations")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(item["user_id"] == str(user_a) for item in data)



def test_search_availability_title_filter_is_case_insensitive(client):
    resp = client.get("/books/availability", params={"title": "clean"})
    assert resp.status_code == 200
    ids = {b["id"] for b in resp.json()}
    assert str(main.book_id) in ids


    main.BOOKS[main.book_id]["reserved_count"] = main.BOOKS[main.book_id]["total_copies"]
    resp2 = client.get("/books/availability", params={"title": "CLEAN"})
    assert resp2.status_code == 200
    ids2 = {b["id"] for b in resp2.json()}
    assert str(main.book_id) not in ids2
