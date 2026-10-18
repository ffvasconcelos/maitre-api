from uuid import UUID, uuid4

from sqlalchemy import Enum as SqlAlchemyEnum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from maitre_api.domain.enums import OrderStatus
from maitre_api.infrastructure.database.base import BaseModel


class Order(BaseModel):
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    table_id: Mapped[UUID] = mapped_column(ForeignKey("tables.id"), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        SqlAlchemyEnum(OrderStatus, name="order_status"),
        default=OrderStatus.OPEN,
        nullable=False,
    )

    items: Mapped[list["OrderItem"]] = relationship(  # noqa: F821 # type: ignore
        back_populates="order",
        cascade="all, delete-orphan",
    )

    table: Mapped["Table"] = relationship()  # noqa: F821 # type: ignore
