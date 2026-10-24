from decimal import Decimal

import pytest

from maitre_api.domain.entities import Order, OrderItem, Product, Table
from maitre_api.domain.enums import OrderStatus, TableStatus
from maitre_api.domain.exceptions.order import OrderNotOpen
from maitre_api.domain.exceptions.table import TableNotAvailable


def test_table_can_be_occupied_released_and_reoccupied() -> None:
    table = Table(number=7, capacity=4)

    table.occupy()
    assert table.status == TableStatus.OCCUPIED
    table.release()
    assert table.status == TableStatus.AVAILABLE
    table.occupy()
    assert table.status == TableStatus.OCCUPIED


def test_occupied_table_rejects_another_occupation() -> None:
    table = Table(number=7, capacity=4, status=TableStatus.OCCUPIED)

    with pytest.raises(TableNotAvailable) as raised:
        table.occupy()

    assert raised.value.number == table.number
    assert table.status == TableStatus.OCCUPIED


@pytest.mark.parametrize(
    "operation, expected",
    [("close", OrderStatus.CLOSED), ("cancel", OrderStatus.CANCELLED)],
)
def test_open_order_can_be_finished(operation: str, expected: OrderStatus) -> None:
    order = Order(table=Table(number=7, capacity=4))

    getattr(order, operation)()

    assert order.status == expected


@pytest.mark.parametrize("status", [OrderStatus.CLOSED, OrderStatus.CANCELLED])
@pytest.mark.parametrize("operation", ["close", "cancel", "add_items"])
def test_finished_order_rejects_mutations(status: OrderStatus, operation: str) -> None:
    order = Order(table=Table(number=7, capacity=4), status=status)

    with pytest.raises(OrderNotOpen) as raised:
        if operation == "add_items":
            order.add_items([])
        else:
            getattr(order, operation)()

    assert raised.value.id == order.id
    assert order.status == status
    assert order.items == []


def test_open_order_appends_items_without_changing_the_price_snapshot() -> None:
    product = Product(name="Soup", price=Decimal("8.50"))
    item = OrderItem(product=product, quantity=2, unit_price=product.price)
    first = Order(table=Table(number=7, capacity=4))
    second = Order(table=Table(number=8, capacity=4))

    first.add_items([item])
    product.price = Decimal("9.50")

    assert first.items == [item]
    assert item.unit_price == Decimal("8.50")
    assert second.items == []
