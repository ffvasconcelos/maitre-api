from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from maitre_api.domain.enums import TableStatus
from maitre_api.domain.exceptions.table import TableNumberAlreadyExists
from maitre_api.infrastructure.database.models.table import Table
from maitre_api.infrastructure.repositories.table_repository import TableRepository
from maitre_api.main import app
from maitre_api.presentation.http.dependencies import get_db


@pytest.fixture
def database_client(integration_session_factory: sessionmaker[Session]):
    def override_db():
        with integration_session_factory() as session:
            yield session

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


@pytest.mark.parametrize("action", ["close", "cancel"])
def test_order_lifecycle_serializes_persisted_entities(
    database_client: TestClient, action: str
) -> None:
    client = database_client
    table_response = client.post(
        "/tables", json={"number": uuid4().int % 1_000_000 + 1, "capacity": 4}
    )
    assert table_response.status_code == 201
    table = table_response.json()
    product_response = client.post("/products", json={"name": "Soup", "price": "8.50"})
    assert product_response.status_code == 201
    product = product_response.json()
    assert product["active"] is True
    assert product["description"] is None

    payload = {
        "table_id": table["id"],
        "items": [{"product_id": product["id"], "quantity": 2}],
    }
    created = client.post("/orders", json=payload)
    assert created.status_code == 201
    order = created.json()
    assert order["table_number"] == table["number"]
    assert order["items"][0]["product_name"] == "Soup"
    assert Decimal(order["items"][0]["subtotal"]) == Decimal("17.00")
    assert client.post("/orders", json=payload).status_code == 409
    assert client.get(f"/orders/{order['id']}").json() == order

    added = client.post(
        f"/orders/{order['id']}/items",
        json=[{"product_id": product["id"], "quantity": 1}],
    )
    assert added.status_code == 201
    assert len(added.json()["items"]) == 2
    listed = client.get("/orders", params={"table_id": table["id"], "status": "Aberto"})
    assert listed.status_code == 200
    assert [entry["id"] for entry in listed.json()] == [order["id"]]

    finished = client.post(f"/orders/{order['id']}/{action}")
    assert finished.status_code == 200
    assert finished.json()["status"] == (
        "Fechado" if action == "close" else "Cancelado"
    )
    assert client.post(f"/orders/{order['id']}/{action}").status_code == 409
    assert client.post(f"/orders/{order['id']}/items", json=[]).status_code == 409
    freed = client.get(f"/tables/{table['id']}")
    assert freed.json()["status"] == TableStatus.AVAIALABLE.value
    assert client.post("/orders", json=payload).status_code == 201


def test_invalid_product_rolls_back_table_occupation(
    database_client: TestClient,
) -> None:
    client = database_client
    created = client.post(
        "/tables", json={"number": uuid4().int % 1_000_000 + 1, "capacity": 4}
    )
    assert created.status_code == 201
    table = created.json()

    rejected = client.post(
        "/orders",
        json={
            "table_id": table["id"],
            "items": [{"product_id": str(uuid4()), "quantity": 1}],
        },
    )

    assert rejected.status_code == 404
    assert client.get(f"/tables/{table['id']}").json()["status"] == (
        TableStatus.AVAIALABLE.value
    )
    assert client.get("/orders", params={"table_id": table["id"]}).json() == []
    assert (
        client.post("/orders", json={"table_id": table["id"], "items": []}).status_code
        == 201
    )


@pytest.mark.parametrize("number", [0, -1])
def test_migrated_database_rejects_nonpositive_table_number(
    integration_session_factory: sessionmaker[Session], number: int
) -> None:
    with integration_session_factory() as session:
        session.add(Table(number=number, capacity=4))
        with pytest.raises(IntegrityError, match="check_table_number_gt_0"):
            session.commit()
        session.rollback()
        assert session.scalar(select(Table).where(Table.number == number)) is None


def test_concurrent_table_creation_returns_created_and_conflict(
    database_client: TestClient,
    integration_session_factory: sessionmaker[Session],
    monkeypatch,
) -> None:
    number = 300_000_000
    barrier = Barrier(2)
    original_lookup = TableRepository.get_by_number

    def synchronized_lookup(self, table_number, for_update=False):
        self.session.execute(text("SET LOCAL lock_timeout = '5s'"))
        table = original_lookup(self, table_number, for_update=for_update)
        assert table is None
        barrier.wait(timeout=5)
        return table

    payload = {"number": number, "capacity": 4}
    with monkeypatch.context() as concurrent_patch:
        concurrent_patch.setattr(TableRepository, "get_by_number", synchronized_lookup)
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(database_client.post, "/tables", json=payload)
                for _ in range(2)
            ]
            responses = [future.result(timeout=10) for future in futures]

    assert sorted(response.status_code for response in responses) == [201, 409]
    conflict = next(response for response in responses if response.status_code == 409)
    assert conflict.json() == {"detail": str(TableNumberAlreadyExists(number))}
    with integration_session_factory() as session:
        assert (
            session.scalar(
                select(func.count()).select_from(Table).where(Table.number == number)
            )
            == 1
        )

    assert database_client.post("/tables", json=payload).status_code == 409
    assert (
        database_client.post(
            "/tables", json={"number": number + 1, "capacity": 4}
        ).status_code
        == 201
    )
