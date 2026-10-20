from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from maitre_api.application.schemas.order import (
    OrderCreate,
    OrderFilter,
    OrderItemCreate,
)
from maitre_api.application.services.order_service import OrderService
from maitre_api.domain.enums import OrderStatus, TableStatus
from maitre_api.domain.exceptions.order import OrderDoesNotExists, OrderNotOpen
from maitre_api.domain.exceptions.product import ProductNotActive, ProductNotFound
from maitre_api.domain.exceptions.table import TableNotAvaiable, TableNotFound
from maitre_api.infrastructure.database.models.order import Order


def make_service() -> tuple[OrderService, MagicMock]:
    uow = MagicMock()
    uow.__enter__.return_value = uow
    return OrderService(uow), uow


def test_create_order_occupies_table_and_snapshots_product_price() -> None:
    service, uow = make_service()
    table_id = uuid4()
    product_id = uuid4()
    table = MagicMock(status=TableStatus.AVAIALABLE, number=7)
    product = MagicMock(active=True, price=Decimal("8.50"))
    uow.tables.get_by_id_for_update.return_value = table
    uow.products.get_by_id.return_value = product
    order_data = OrderCreate(
        table_id=table_id,
        items=[OrderItemCreate(product_id=product_id, quantity=2)],
    )
    uow.orders.add.side_effect = lambda order: order

    result = service.create_order(order_data)

    assert isinstance(result, Order)
    assert result.table_id == table_id
    assert len(result.items) == 1
    assert result.items[0].product is product
    assert result.items[0].quantity == 2
    assert result.items[0].unit_price == Decimal("8.50")
    uow.tables.occupy_table.assert_called_once_with(table_id)
    uow.tables.get_by_id_for_update.assert_called_once_with(table_id)
    uow.commit.assert_called_once_with()


def test_create_order_rejects_missing_table() -> None:
    service, uow = make_service()
    table_id = uuid4()
    uow.tables.get_by_id_for_update.return_value = None

    with pytest.raises(TableNotFound):
        service.create_order(OrderCreate(table_id=table_id, items=[]))

    uow.tables.get_by_id_for_update.assert_called_once_with(table_id)
    uow.tables.occupy_table.assert_not_called()
    uow.commit.assert_not_called()


def test_create_order_rejects_occupied_table() -> None:
    service, uow = make_service()
    table_id = uuid4()
    uow.tables.get_by_id_for_update.return_value = MagicMock(
        status=TableStatus.OCCUPIED, number=7
    )

    with pytest.raises(TableNotAvaiable):
        service.create_order(OrderCreate(table_id=table_id, items=[]))

    uow.tables.get_by_id_for_update.assert_called_once_with(table_id)
    uow.tables.occupy_table.assert_not_called()
    uow.commit.assert_not_called()


@pytest.mark.parametrize("active", [True, False])
def test_create_order_requires_existing_active_products(active: bool) -> None:
    service, uow = make_service()
    table_id = uuid4()
    product_id = uuid4()
    uow.tables.get_by_id_for_update.return_value = MagicMock(
        status=TableStatus.AVAIALABLE
    )
    uow.products.get_by_id.return_value = (
        MagicMock(active=True, price=Decimal("2.00")) if active else None
    )
    order_data = OrderCreate(
        table_id=table_id,
        items=[OrderItemCreate(product_id=product_id, quantity=1)],
    )

    expected_exception = ProductNotFound if active is False else None
    if expected_exception:
        with pytest.raises(expected_exception):
            service.create_order(order_data)
    else:
        uow.products.get_by_id.return_value.active = False
        with pytest.raises(ProductNotActive):
            service.create_order(order_data)

    uow.tables.get_by_id_for_update.assert_called_once_with(table_id)
    uow.orders.add.assert_not_called()
    uow.commit.assert_not_called()


def test_get_order_returns_existing_order() -> None:
    service, uow = make_service()
    order_id = uuid4()
    order = Order(table_id=uuid4())
    uow.orders.get_by_id.return_value = order

    assert service.get_order_by_id(order_id) is order
    uow.orders.get_by_id.assert_called_once_with(order_id)
    uow.commit.assert_not_called()


def test_get_order_rejects_missing_order() -> None:
    service, uow = make_service()
    uow.orders.get_by_id.return_value = None

    with pytest.raises(OrderDoesNotExists):
        service.get_order_by_id(uuid4())


def test_add_order_items_appends_validated_items_and_commits() -> None:
    service, uow = make_service()
    order_id = uuid4()
    product_id = uuid4()
    order = Order(table_id=uuid4(), status=OrderStatus.OPEN)
    uow.orders.get_by_id.return_value = order
    uow.products.get_by_id.return_value = MagicMock(active=True, price=Decimal("4.25"))
    uow.orders.add_items.return_value = order

    result = service.add_order_items(
        order_id, [OrderItemCreate(product_id=product_id, quantity=3)]
    )

    assert result is order
    appended_items = uow.orders.add_items.call_args.args[1]
    assert len(appended_items) == 1
    assert appended_items[0].quantity == 3
    assert appended_items[0].unit_price == Decimal("4.25")
    uow.commit.assert_called_once_with()


def test_add_order_items_rejects_missing_or_closed_order() -> None:
    service, uow = make_service()
    order_id = uuid4()
    uow.orders.get_by_id.return_value = None

    with pytest.raises(OrderDoesNotExists):
        service.add_order_items(order_id, [])

    uow.orders.get_by_id.return_value = Order(
        table_id=uuid4(), status=OrderStatus.CLOSED
    )
    with pytest.raises(OrderNotOpen):
        service.add_order_items(order_id, [])

    uow.orders.add_items.assert_not_called()
    uow.commit.assert_not_called()


def test_list_orders_forwards_filter_without_committing() -> None:
    service, uow = make_service()
    order_filter = OrderFilter(status=OrderStatus.OPEN)
    orders = [Order(table_id=uuid4())]
    uow.orders.list.return_value = orders

    assert service.list_orders(order_filter) is orders
    uow.orders.list.assert_called_once_with(order_filter)
    uow.commit.assert_not_called()


@pytest.mark.parametrize(
    ("operation", "repository_method", "expected_status"),
    [
        ("close_order", "close", OrderStatus.CLOSED),
        ("cancel_order", "cancel", OrderStatus.CANCELLED),
    ],
)
def test_finish_order_updates_status_and_frees_table(
    operation: str, repository_method: str, expected_status: OrderStatus
) -> None:
    service, uow = make_service()
    order_id = uuid4()
    table = MagicMock()
    order = Order(table_id=uuid4(), table=table, status=OrderStatus.OPEN)
    uow.orders.get_by_id.return_value = order
    repository_action = getattr(uow.orders, repository_method)

    def finish(value: Order) -> Order:
        value.status = expected_status
        return value

    repository_action.side_effect = finish

    assert getattr(service, operation)(order_id) is order

    repository_action.assert_called_once_with(order)
    assert order.status == expected_status
    uow.tables.free_table.assert_called_once_with(table)
    uow.commit.assert_called_once_with()


@pytest.mark.parametrize("operation", ["close_order", "cancel_order"])
def test_finish_order_rejects_missing_or_non_open_order(operation: str) -> None:
    service, uow = make_service()
    order_id = uuid4()
    uow.orders.get_by_id.return_value = None

    with pytest.raises(OrderDoesNotExists):
        getattr(service, operation)(order_id)

    uow.orders.get_by_id.return_value = Order(
        table_id=uuid4(), status=OrderStatus.CANCELLED
    )
    with pytest.raises(OrderNotOpen):
        getattr(service, operation)(order_id)

    uow.tables.free_table.assert_not_called()
    uow.commit.assert_not_called()
