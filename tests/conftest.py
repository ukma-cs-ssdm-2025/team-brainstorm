import pytest
from fastapi.testclient import TestClient
from src.api.main import app

@pytest.fixture
def client():
    """Фікстура для створення тестового клієнта FastAPI"""
    with TestClient(app) as c:
        yield c
