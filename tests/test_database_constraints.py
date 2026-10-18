from sqlalchemy import CheckConstraint

from maitre_api.infrastructure.database.models.order_item import OrderItem
from maitre_api.infrastructure.database.models.table import Table


def check_expressions(model: type) -> set[str]:
    return {
        str(constraint.sqltext)
        for column in model.__table__.columns
        for constraint in column.constraints
        if isinstance(constraint, CheckConstraint)
    }


def test_order_item_requires_positive_quantity() -> None:
    assert "quantity > 0" in check_expressions(OrderItem)


def test_table_requires_positive_capacity() -> None:
    assert "capacity > 0" in check_expressions(Table)