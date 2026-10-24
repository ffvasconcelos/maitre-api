from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import Session, sessionmaker

from maitre_api.application.schemas.order import (
    OrderCreate,
    OrderFilter,
    OrderItemCreate,
    OrderResponse,
)
from maitre_api.application.schemas.product import ProductCreate, ProductResponse
from maitre_api.application.schemas.table import TableCreate, TableResponse
from maitre_api.application.services import OrderService, ProductService, TableService
from maitre_api.domain.entities import Order, OrderItem, Product, Table
from maitre_api.domain.enums import OrderStatus, TableStatus
from maitre_api.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


@pytest.mark.parametrize("expire_on_commit", [False, True])
def test_domain_results_are_serializable_after_session_closes(
    integration_session_factory: sessionmaker[Session], expire_on_commit: bool
) -> None:
    factory = integration_session_factory
    with factory(expire_on_commit=expire_on_commit) as session:
        uow = SqlAlchemyUnitOfWork(session)
        table = TableService(uow).create_table(
            TableCreate(number=uuid4().int % 1_000_000 + 1, capacity=4)
        )
        product = ProductService(uow).create_product(
            ProductCreate(name="Soup", price=Decimal("8.50"))
        )
        service = OrderService(uow)
        created = service.create_order(
            OrderCreate(
                table_id=table.id,
                items=[OrderItemCreate(product_id=product.id, quantity=2)],
            )
        )
        added = service.add_order_items(
            created.id, [OrderItemCreate(product_id=product.id, quantity=1)]
        )
        fetched = service.get_order_by_id(created.id)
        listed = service.list_orders(OrderFilter(table_id=table.id))
        closed = service.close_order(created.id)

    assert isinstance(table, Table)
    assert isinstance(product, Product)
    assert inspect(table, raiseerr=False) is None
    assert inspect(product, raiseerr=False) is None
    assert TableResponse.model_validate(table).number == table.number
    assert ProductResponse.model_validate(product).price == Decimal("8.50")
    for order, item_count in [
        (created, 1),
        (added, 2),
        (fetched, 2),
        (listed[0], 2),
        (closed, 2),
    ]:
        assert isinstance(order, Order)
        assert inspect(order, raiseerr=False) is None
        assert isinstance(order.table, Table)
        assert all(isinstance(item, OrderItem) for item in order.items)
        assert all(isinstance(item.product, Product) for item in order.items)
        assert all(inspect(item, raiseerr=False) is None for item in order.items)
        response = OrderResponse.model_validate(order)
        assert response.table_number == table.number
        assert len(response.items) == item_count
        assert response.items[0].product_name == "Soup"
        assert sum(item.subtotal for item in response.items) == (
            Decimal("17.00") + (item_count - 1) * Decimal("8.50")
        )
        assert order.created_at is not None
        assert order.items[0].created_at is not None
    assert closed.status == OrderStatus.CLOSED
    assert closed.table.status == TableStatus.AVAIALABLE

    # Domain values remain independent snapshots of the state read by each use case.
    assert fetched.status == OrderStatus.OPEN
    assert fetched.table.status == TableStatus.OCCUPIED
