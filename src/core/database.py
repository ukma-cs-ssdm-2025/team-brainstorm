from uuid import uuid4
from threading import Lock


DB_LOCK = Lock()
BOOKS = {}
RESERVATIONS = {}
USERS = {}


# додано тестову книгу
book_id = uuid4()
BOOKS[book_id] = {
    "id": book_id,
    "isbn": "978-3-16-148410-0",
    "title": "Clean Code",
    "author": "Robert C. Martin",
    "total_copies": 3,
    "reserved_count": 0,

}
