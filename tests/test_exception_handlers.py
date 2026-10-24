from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from maitre_api.application.services.product_service import ProductService
from maitre_api.domain.exceptions.product import ProductNotFound
from maitre_api.main import app
from maitre_api.presentation.http.dependencies import get_product_service


@pytest.fixture
def product_service():
    previous_overrides = app.dependency_overrides.copy()
    service = MagicMock(spec=ProductService)
    app.dependency_overrides[get_product_service] = lambda: service
    try:
        yield service
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


def test_domain_error_subclasses_use_the_registered_handler(product_service) -> None:
    class MissingProduct(ProductNotFound):
        pass

    exception = MissingProduct(uuid4())
    product_service.get_product.side_effect = exception

    with TestClient(app) as client:
        response = client.get(f"/products/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"code": "product_not_found", "detail": str(exception)}


def test_unexpected_errors_remain_internal_server_errors(product_service) -> None:
    product_service.get_product.side_effect = RuntimeError("internal database details")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(f"/products/{uuid4()}")

    assert response.status_code == 500
    assert response.text == "Internal Server Error"


@pytest.mark.parametrize(
    "method, path, statuses",
    [
        ("post", "/orders", ["404", "409"]),
        ("post", "/orders/{order_id}/items", ["404", "409"]),
        ("post", "/orders/{order_id}/close", ["404", "409"]),
        ("post", "/orders/{order_id}/cancel", ["404", "409"]),
        ("get", "/orders/{order_id}", ["404"]),
        ("get", "/products/{product_id}", ["404"]),
        ("post", "/tables", ["409"]),
        ("get", "/tables/{table_id}", ["404"]),
        ("get", "/tables/by_number/{number}", ["404"]),
    ],
)
def test_openapi_documents_domain_errors(
    method: str, path: str, statuses: list[str]
) -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    responses = schema["paths"][path][method]["responses"]
    for status_code in statuses:
        assert responses[status_code]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorResponse"
        }
    error_schema = schema["components"]["schemas"]["ErrorResponse"]
    assert set(error_schema["required"]) == {"code", "detail"}
    assert error_schema["properties"]["code"]["type"] == "string"
    assert error_schema["properties"]["detail"]["type"] == "string"
    assert responses["422"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/HTTPValidationError"
    }
