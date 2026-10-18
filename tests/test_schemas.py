from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from maitre_api.application.schemas.order import OrderItemCreate, OrderItemResponse


def test_order_item_response_computes_subtotal() -> None:
    timestamp = datetime.now(UTC)
    response = OrderItemResponse(
        id=uuid4(),
        product_id=uuid4(),
        product={"name": "Soup"},
        quantity=3,
        unit_price=Decimal("2.50"),
        created_at=timestamp,
        updated_at=timestamp,
    )

    assert response.subtotal == Decimal("7.50")


@pytest.mark.parametrize("quantity", [0, -1])
def test_order_item_create_requires_positive_quantity(quantity: int) -> None:
    with pytest.raises(ValidationError):
        OrderItemCreate(product_id=uuid4(), quantity=quantity)
