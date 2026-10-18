from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from maitre_api.application.schemas.order import OrderFilter
from maitre_api.domain.enums import OrderStatus
from maitre_api.infrastructure.database.models.order import Order
from maitre_api.infrastructure.database.models.order_item import OrderItem
from maitre_api.infrastructure.repositories.order_repository import OrderRepository


def test_add_items_appends_all_items_to_order() -> None:
    session = MagicMock(spec=Session)
    repository = OrderRepository(session)
    order = Order(table_id=uuid4(), items=[])
    items = [
        OrderItem(quantity=1, unit_price=Decimal("8.50")),
        OrderItem(quantity=2, unit_price=Decimal("3.25")),
    ]

    result = repository.add_items(order, items)

    assert result is order
    assert order.items == items
    session.flush.assert_called_once_with()


def test_get_by_id_eager_loads_items_and_products() -> None:
    session = MagicMock(spec=Session)
    repository = OrderRepository(session)
    order = Order(table_id=uuid4())
    session.scalars.return_value.one_or_none.return_value = order
    order_id = uuid4()

    assert repository.get_by_id(order_id) is order
    session.scalars.return_value.one_or_none.assert_called_once_with()
    statement = session.scalars.call_args.args[0]
    assert statement.column_descriptions[0]["entity"] is Order
    assert "orders.id = :id_1" in str(statement)


def test_get_open_by_table_id_filters_by_open_status() -> None:
    session = MagicMock(spec=Session)
    repository = OrderRepository(session)
    order = Order(table_id=uuid4())
    session.scalar.return_value = order

    assert repository.get_open_by_table_id(order.table_id) is order
    statement = session.scalar.call_args.args[0]
    assert "orders.table_id = :table_id_1" in str(statement)
    assert "orders.status = :status_1" in str(statement)


def test_add_flushes_order() -> None:
    session = MagicMock(spec=Session)
    repository = OrderRepository(session)
    order = Order(table_id=uuid4())

    assert repository.add(order) is order
    session.add.assert_called_once_with(order)
    session.flush.assert_called_once_with()


def test_list_applies_all_non_null_filters() -> None:
    session = MagicMock(spec=Session)
    repository = OrderRepository(session)
    results = [Order(table_id=uuid4())]
    session.scalars.return_value.all.return_value = results
    table_id = uuid4()

    order_filter = OrderFilter(table_id=table_id, status=OrderStatus.OPEN)
    assert repository.list(order_filter) is results
    statement = session.scalars.call_args.args[0]
    assert "orders.table_id = :table_id_1" in str(statement)
    assert "orders.status = :status_1" in str(statement)


def test_list_without_filters_selects_all_orders() -> None:
    session = MagicMock(spec=Session)
    repository = OrderRepository(session)
    session.scalars.return_value.all.return_value = []

    assert repository.list(OrderFilter()) == []
    assert str(session.scalars.call_args.args[0]) == str(select(Order))


def test_close_and_cancel_update_status_and_flush() -> None:
    session = MagicMock(spec=Session)
    repository = OrderRepository(session)
    order = Order(table_id=uuid4(), status=OrderStatus.OPEN)

    assert repository.close(order) is order
    assert order.status == OrderStatus.CLOSED
    assert repository.cancel(order) is order
    assert order.status == OrderStatus.CANCELLED
    assert session.flush.call_count == 2
