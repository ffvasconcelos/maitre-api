from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from maitre_api.application.services.order_service import OrderService
from maitre_api.application.services.product_service import ProductService
from maitre_api.application.services.table_service import TableService
from maitre_api.domain.exceptions.order import OrderDoesNotExists, OrderNotOpen
from maitre_api.domain.exceptions.product import ProductNotActive, ProductNotFound
from maitre_api.domain.exceptions.table import (
    TableNotAvaiable,
    TableNotFound,
    TableNumberAlreadyExists,
    TableNumberNotFound,
)
from maitre_api.main import app
from maitre_api.presentation.http.dependencies import (
    get_order_service,
    get_product_service,
    get_table_service,
)

client = TestClient(app)
created_at = datetime(2026, 1, 1, tzinfo=UTC).isoformat()


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def install_service(dependency, service: MagicMock) -> None:
    app.dependency_overrides[dependency] = lambda: service


def product_response() -> dict:
    return {
        "id": str(uuid4()),
        "name": "Soup",
        "description": "Daily special",
        "price": "8.50",
        "active": True,
        "created_at": created_at,
        "updated_at": created_at,
    }


def table_response() -> dict:
    return {
        "id": str(uuid4()),
        "number": 7,
        "capacity": 4,
        "status": "disponível",
        "created_at": created_at,
        "updated_at": created_at,
    }


def order_response() -> dict:
    return {
        "id": str(uuid4()),
        "table_id": str(uuid4()),
        "table": {"number": 7},
        "status": "Aberto",
        "items": [],
        "created_at": created_at,
        "updated_at": created_at,
    }


def test_product_routes_create_list_and_get() -> None:
    service = MagicMock(spec=ProductService)
    product = product_response()
    service.create_product.return_value = product
    service.list_products.return_value = [product]
    service.get_product.return_value = product
    install_service(get_product_service, service)

    created = client.post(
        "/products",
        json={"name": "Soup", "description": "Daily special", "price": "8.50"},
    )
    listed = client.get("/products")
    fetched = client.get(f"/products/{product['id']}")

    assert created.status_code == 201
    assert created.json()["name"] == "Soup"
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert fetched.status_code == 200
    service.create_product.assert_called_once()
    assert service.get_product.call_args.args[0].__str__() == product["id"]


def test_get_missing_product_returns_404() -> None:
    service = MagicMock(spec=ProductService)
    service.get_product.side_effect = ProductNotFound(uuid4())
    install_service(get_product_service, service)

    response = client.get(f"/products/{uuid4()}")

    assert response.status_code == 404


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": "x" * 151},
        {"description": "x" * 251},
        {"price": "100000000.00"},
        {"price": "1.001"},
        {"active": None},
    ],
)
def test_create_product_rejects_values_outside_storage_contract(
    overrides: dict,
) -> None:
    service = MagicMock(spec=ProductService)
    install_service(get_product_service, service)

    response = client.post(
        "/products", json={"name": "Soup", "price": "8.50", **overrides}
    )

    assert response.status_code == 422
    service.create_product.assert_not_called()


def test_table_routes_create_list_and_get_by_id_or_number() -> None:
    service = MagicMock(spec=TableService)
    table = table_response()
    service.create_table.return_value = table
    service.list_tables.return_value = [table]
    service.get_table_by_id.return_value = table
    service.get_table_by_number.return_value = table
    install_service(get_table_service, service)

    created = client.post("/tables", json={"number": 7, "capacity": 4})
    listed = client.get("/tables")
    fetched_by_id = client.get(f"/tables/{table['id']}")
    fetched_by_number = client.get("/tables/by_number/7")

    assert created.status_code == 201
    assert listed.status_code == 200
    assert fetched_by_id.status_code == 200
    assert fetched_by_number.status_code == 200
    assert service.get_table_by_number.call_args.args == (7,)


@pytest.mark.parametrize(
    ("path", "exception"),
    [
        ("/tables", TableNumberAlreadyExists(7)),
        ("/tables/by_number/7", TableNumberNotFound(7)),
        (f"/tables/{uuid4()}", TableNotFound(uuid4())),
    ],
)
def test_table_routes_map_domain_errors_to_http_conflicts_and_not_found(
    path: str, exception: Exception
) -> None:
    service = MagicMock(spec=TableService)
    install_service(get_table_service, service)
    if path == "/tables":
        service.create_table.side_effect = exception
        response = client.post("/tables", json={"number": 7, "capacity": 4})
        assert response.status_code == 409
    elif "/by_number/" in path:
        service.get_table_by_number.side_effect = exception
        response = client.get(path)
        assert response.status_code == 404
    else:
        service.get_table_by_id.side_effect = exception
        response = client.get(path)
        assert response.status_code == 404


def test_create_order_returns_created_order() -> None:
    service = MagicMock(spec=OrderService)
    order = order_response()
    service.create_order.return_value = order
    install_service(get_order_service, service)

    response = client.post(
        "/orders",
        json={"table_id": str(uuid4()), "items": []},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "Aberto"
    service.create_order.assert_called_once()


@pytest.mark.parametrize(
    ("exception", "status_code"),
    [
        (ProductNotActive(uuid4()), 409),
        (TableNotAvaiable(7), 409),
        (ProductNotFound(uuid4()), 404),
        (TableNotFound(uuid4()), 404),
    ],
)
def test_create_order_maps_domain_errors(
    exception: Exception, status_code: int
) -> None:
    service = MagicMock(spec=OrderService)
    service.create_order.side_effect = exception
    install_service(get_order_service, service)

    response = client.post("/orders", json={"table_id": str(uuid4()), "items": []})

    assert response.status_code == status_code


@pytest.mark.parametrize(
    ("exception", "status_code"),
    [
        (ProductNotActive(uuid4()), 409),
        (OrderNotOpen(uuid4()), 409),
        (ProductNotFound(uuid4()), 404),
        (OrderDoesNotExists(uuid4()), 404),
    ],
)
def test_add_order_items_maps_domain_errors(
    exception: Exception, status_code: int
) -> None:
    service = MagicMock(spec=OrderService)
    service.add_order_items.side_effect = exception
    install_service(get_order_service, service)

    response = client.post(f"/orders/{uuid4()}/items", json=[])

    assert response.status_code == status_code


@pytest.mark.parametrize("action", ["close", "cancel"])
@pytest.mark.parametrize(
    ("exception", "status_code"),
    [(OrderDoesNotExists(uuid4()), 404), (OrderNotOpen(uuid4()), 409)],
)
def test_finish_order_routes_map_domain_errors(
    action: str, exception: Exception, status_code: int
) -> None:
    service = MagicMock(spec=OrderService)
    getattr(service, f"{action}_order").side_effect = exception
    install_service(get_order_service, service)

    response = client.post(f"/orders/{uuid4()}/{action}")

    assert response.status_code == status_code


def test_list_orders_passes_query_filters_to_service() -> None:
    service = MagicMock(spec=OrderService)
    order = order_response()
    service.list_orders.return_value = [order]
    install_service(get_order_service, service)

    response = client.get(f"/orders?table_id={order['table_id']}&status=Aberto")

    assert response.status_code == 200
    assert response.json()[0]["table_number"] == 7
    assert service.list_orders.call_args.args[0].table_id.__str__() == order["table_id"]


def test_get_missing_order_returns_404() -> None:
    service = MagicMock(spec=OrderService)
    service.get_order_by_id.side_effect = OrderDoesNotExists(uuid4())
    install_service(get_order_service, service)

    response = TestClient(app, raise_server_exceptions=False).get(f"/orders/{uuid4()}")

    assert response.status_code == 404


def test_get_existing_order_returns_order_response() -> None:
    service = MagicMock(spec=OrderService)
    order = order_response()
    service.get_order_by_id.return_value = order
    install_service(get_order_service, service)

    response = client.get(f"/orders/{order['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == order["id"]
