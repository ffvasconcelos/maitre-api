from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from maitre_api.infrastructure.database.base import BaseModel


class OrderItem(BaseModel):
    __tablename__ = "order_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[Integer] = mapped_column(
        Integer, CheckConstraint("number > 0", name="check_quantity_gt_0")
    )
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
