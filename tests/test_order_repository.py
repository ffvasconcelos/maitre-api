from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from maitre_api.application.schemas.order import OrderFilter
from maitre_api.domain.entities import Order, OrderItem, Product, Table
from maitre_api.domain.enums import OrderStatus, TableStatus
from maitre_api.infrastructure.database.models.order import Order as OrderModel
from maitre_api.infrastructure.database.models.order_item import (
    OrderItem as OrderItemModel,
)
from maitre_api.infrastructure.database.models.product import Product as ProductModel
from maitre_api.infrastructure.database.models.table import Table as TableModel
from maitre_api.infrastructure.repositories.order_repository import OrderRepository


def make_order() -> Order:
    return Order(table=Table(number=7, capacity=4))


def make_model() -> OrderModel:
    table = TableModel(id=uuid4(), number=7, capacity=4, status=TableStatus.OCCUPIED)
    product = ProductModel(id=uuid4(), name="Soup", price=Decimal("8.50"), active=True)
    return OrderModel(
        id=uuid4(),
        table_id=table.id,
        table=table,
        status=OrderStatus.OPEN,
        items=[
            OrderItemModel(
                id=uuid4(),
                product_id=product.id,
                product=product,
                quantity=2,
                unit_price=Decimal("8.50"),
            )
        ],
    )


def test_add_items_persists_models_and_returns_domain_items() -> None:
    session = MagicMock(spec=Session)
    repository = OrderRepository(session)
    order = make_order()
    model = OrderModel(id=order.id, table_id=order.table_id, items=[])
    session.get.return_value = model
    items = [
        OrderItem(
            product=Product(name="Soup", price=Decimal("8.50")),
            quantity=1,
            unit_price=Decimal("8.50"),
        ),
        OrderItem(
            product=Product(name="Tea", price=Decimal("3.25")),
            quantity=2,
            unit_price=Decimal("3.25"),
        ),
    ]

    result = repository.add_items(order, items)

    assert result is order
    assert order.items == items
    assert len(model.items) == 2
    for entity, row in zip(items, model.items, strict=True):
        assert isinstance(row, OrderItemModel)
        assert row.id == entity.id
        assert row.product_id == entity.product_id
        assert row.quantity == entity.quantity
        assert row.unit_price == entity.unit_price
    session.get.assert_called_once_with(OrderModel, order.id)
    session.flush.assert_called_once_with()


@pytest.mark.parametrize("found", [False, True])
def test_get_by_id_returns_domain_order_with_relations(found: bool) -> None:
    session = MagicMock(spec=Session)
    repository = OrderRepository(session)
    model = make_model() if found else None
    session.scalars.return_value.one_or_none.return_value = model
    order_id = uuid4()

    result = repository.get_by_id(order_id)

    if found:
        assert isinstance(result, Order)
        assert isinstance(result.table, Table)
        assert isinstance(result.items[0], OrderItem)
        assert isinstance(result.items[0].product, Product)
        assert result.id == model.id
        assert result.table_id == model.table_id
        assert result.items[0].product_id == model.items[0].product_id
        assert result.items[0].quantity == 2
        assert result.items[0].unit_price == Decimal("8.50")
    else:
        assert result is None
    statement = session.scalars.call_args.args[0]
    assert statement.column_descriptions[0]["entity"] is OrderModel
    assert "orders.id = :id_1" in str(statement)


@pytest.mark.parametrize("found", [False, True])
def test_get_open_by_table_id_filters_by_open_status(found: bool) -> None:
    session = MagicMock(spec=Session)
    repository = OrderRepository(session)
    model = make_model() if found else None
    session.scalar.return_value = model

    result = repository.get_open_by_table_id(uuid4())

    if found:
        assert isinstance(result, Order)
        assert result.id == model.id
    else:
        assert result is None
    statement = session.scalar.call_args.args[0]
    assert "orders.table_id = :table_id_1" in str(statement)
    assert "orders.status = :status_1" in str(statement)


def test_add_converts_order_and_items_to_models() -> None:
    session = MagicMock(spec=Session)
    repository = OrderRepository(session)
    order = make_order()
    order.items.append(
        OrderItem(
            product=Product(name="Soup", price=Decimal("8.50")),
            quantity=2,
            unit_price=Decimal("8.50"),
        )
    )

    assert repository.add(order) is order

    model = session.add.call_args.args[0]
    assert isinstance(model, OrderModel)
    assert model.id == order.id
    assert model.table_id == order.table_id
    assert model.status == order.status
    assert model.items[0].id == order.items[0].id
    assert model.items[0].product_id == order.items[0].product_id
    assert model.items[0].quantity == 2
    assert model.items[0].unit_price == Decimal("8.50")
    session.flush.assert_called_once_with()


def test_list_applies_all_non_null_filters() -> None:
    session = MagicMock(spec=Session)
    repository = OrderRepository(session)
    model = make_model()
    session.scalars.return_value.all.return_value = [model]
    order_filter = OrderFilter(table_id=model.table_id, status=OrderStatus.OPEN)

    result = repository.list(order_filter)

    assert len(result) == 1
    assert isinstance(result[0], Order)
    assert result[0].id == model.id
    statement = session.scalars.call_args.args[0]
    assert "orders.table_id = :table_id_1" in str(statement)
    assert "orders.status = :status_1" in str(statement)


def test_list_without_filters_selects_all_orders() -> None:
    session = MagicMock(spec=Session)
    repository = OrderRepository(session)
    session.scalars.return_value.all.return_value = []

    assert repository.list(OrderFilter()) == []
    statement = session.scalars.call_args.args[0]
    assert statement.column_descriptions[0]["entity"] is OrderModel
    assert "WHERE" not in str(statement)


def test_close_and_cancel_update_model_and_domain_status() -> None:
    session = MagicMock(spec=Session)
    repository = OrderRepository(session)
    order = make_order()
    model = OrderModel(id=order.id, table_id=order.table_id, status=order.status)
    session.get.return_value = model

    assert repository.close(order) is order
    assert order.status == model.status == OrderStatus.CLOSED
    assert repository.cancel(order) is order
    assert order.status == model.status == OrderStatus.CANCELLED
    assert session.flush.call_count == 2
