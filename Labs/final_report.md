# Final Project Report — Library Brainstorm | Team Brainstorm (UKMA SSDM 2025)

## Summary

**Library Brainstorm** is a web-based library management platform implemented primarily with FastAPI (async), SQLAlchemy (async), and PostgreSQL (asyncpg). The project provides REST endpoints for managing books, user registration and authentication, reservations, reviews, favorites and reminder generation. The codebase includes a lightweight frontend under `docs/frontend` and comprehensive documentation under `docs/`.

## Technology Stack

- **Backend:** FastAPI, Python (Pydantic v2), SQLAlchemy (async), asyncpg, Alembic (present in requirements)
- **Auth & Security:** JWT (python-jose), password hashing with `passlib[bcrypt]`, custom token helpers in `src/core/security.py`
- **Email:** `aiosmtplib` used for async sending in `src/core/mailer.py`
- **Server:** `uvicorn`
- **Testing:** `pytest` (see `pytest.ini`), tests exercise API endpoints using `fastapi.testclient`
- **Frontend / Static UI:** Minimal static app in `docs/frontend` (HTML/JS/CSS)
- **Docs:** Markdown files under `docs/`, OpenAPI spec at `docs/api/openapi-generated.yaml` (currently empty/placeholder)

## System Functionality (summary)

- Book management: listing, search, update (routes in `src/api/routes/books.py`, model `src/api/models/bookdb.py`).
- User management: register, login, JWT issuance, current-user helpers (`src/api/routes/users.py`, models `src/api/models/user.py`).
- Reservations: create, list (for current user), cancel, clear; reservations persist to DB (`src/api/routes/reservations.py`, `src/api/models/reservation.py`).
- Reviews: add/list/delete reviews with aggregate statistics (`src/api/routes/reviews.py`, `src/api/models/review.py`).
- Favorites: add/list/remove favorite books for a user (`src/api/routes/favorites.py`, `src/api/models/favorite.py`).
- Reminders: endpoint to list near-expiry reservations (`src/api/routes/reminders.py`).
- Email notifications: implemented in `src/core/mailer.py`, used by reservation flow.

## Readiness

### Backend

- [x] Database models present (`src/api/models`) and async engine configured in `src/core/database.py`.
- [x] Main API app configured in `src/api/main.py` and includes all main routers.
- [x] Role-based check for librarian implemented (`require_librarian` in `src/api/routes/users.py`).
- [x] Reservation, review, favorites implemented.

### Frontend

- [x] Minimal static UI and assets available under `docs/frontend/` (HTML/JS/CSS).

## Tests & Coverage

- Tests present in `tests/test_reservations.py`. They exercise health checks, books listing/filtering, user registration/login, reservation create/cancel, reviews, reminders, and password validation.
- `pytest.ini` present; test runner and basic configuration included. Coverage report generation commands are described in `README.md`.
- Coverage percentage not calculated here; run `pytest --cov=src --cov-report=html` locally or in CI to measure.

## Implemented Modules and Mapping (files)

- API entry: `src/api/main.py`
- Routes (endpoints): `src/api/routes/*.py` (books, reservations, users, reviews, reminders, favorites, pdf)
- Models: `src/api/models/*` (Book, User, Reservation, Review, Favorite)
- Core utilities: `src/core/security.py` (password hashing, JWT helpers), `src/core/database.py` (async engine and session maker), `src/core/mailer.py` (async email)
- Services: high-level logic in `src/services/*` (reservations_service.py, user_service.py, reviews_service.py, reminder_service.py)
- Tests: `tests/test_reservations.py`
- Docs & API spec: `docs/api/` and `docs/` content

## Conclusion

The project is a well-structured FastAPI-based library management system with core features implemented: books management, user auth, reservations, reviews, favorites, email notifications, and a basic frontend. Documentation and tests are present. 

---

Report done by: Team Brainstorm 
