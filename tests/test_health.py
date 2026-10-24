from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from maitre_api.main import app
from maitre_api.presentation.http.dependencies import get_db

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_health_check_returns_ok() -> None:
    session = MagicMock()
    app.dependency_overrides[get_db] = lambda: session

    try:
        response = client.get("/health/db")
    finally:
        app.dependency_overrides.pop(get_db)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    session.execute.assert_called_once()


def test_database_health_check_returns_error_when_query_fails() -> None:
    session = MagicMock()
    session.execute.side_effect = RuntimeError("database unavailable")
    app.dependency_overrides[get_db] = lambda: session

    try:
        response = client.get("/health/db")
    finally:
        app.dependency_overrides.pop(get_db)

    assert response.status_code == 503
    assert response.json() == {"detail": "database unavailable"}
