import logging
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

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


@pytest.mark.parametrize(
    "error",
    [
        RuntimeError("internal-host:5432/password=not-public"),
        OperationalError("SELECT 1", {}, RuntimeError("internal connection details")),
    ],
)
def test_database_health_check_hides_details_and_logs_the_failure(
    error, caplog
) -> None:
    session = MagicMock()
    session.execute.side_effect = error
    app.dependency_overrides[get_db] = lambda: session

    try:
        with caplog.at_level(logging.ERROR, logger="maitre_api.main"):
            response = client.get("/health/db")
    finally:
        app.dependency_overrides.pop(get_db)

    assert response.status_code == 503
    assert response.json() == {"detail": "Banco de dados indisponível."}
    assert str(error) not in response.text
    record = next(
        record for record in caplog.records if record.name == "maitre_api.main"
    )
    assert record.levelno == logging.ERROR
    assert record.getMessage() == "Database health check failed"
    assert record.exc_info[1] is error


def test_database_health_failure_is_documented() -> None:
    schema = client.get("/openapi.json").json()
    response = schema["paths"]["/health/db"]["get"]["responses"]["503"]

    assert response["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/HealthErrorResponse"
    }
    assert schema["components"]["schemas"]["HealthErrorResponse"]["required"] == [
        "detail"
    ]
