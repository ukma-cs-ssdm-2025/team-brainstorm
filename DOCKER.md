Dockerized local setup
----------------------

Services
- `backend`: FastAPI app on port 8000
- `frontend`: Nginx serving static UI on port 8080

Usage
- Build and start: `docker compose up --build`
- Stop: `docker compose down`

URLs
- Backend API: `http://localhost:8000` (`/docs` for Swagger)
- Frontend UI: `http://localhost:8080`

Notes
- CORS is enabled in the API for local demo.
- The frontend has an "API Base URL" field to point at a different API if needed.

