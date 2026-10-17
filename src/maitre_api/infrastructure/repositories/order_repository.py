import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from maitre_api.application.schemas.order import OrderFilter
from maitre_api.domain.enums.order_status import OrderStatus
from maitre_api.infrastructure.database.models.order import Order
from maitre_api.infrastructure.database.models.order_item import OrderItem


class OrderRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, id: uuid.UUID) -> Order | None:
        statement = (
            select(Order)
            .options(
                selectinload(Order.items).joinedload(OrderItem.product)
            )
            .where(Order.id == id)
        )

        return self.session.scalars(statement).one_or_none()

    def get_open_by_table_id(self, table_id: uuid.UUID) -> Order | None:
        return self.session.scalar(
            select(Order).where(
                Order.table_id == table_id, Order.status == OrderStatus.OPEN
            )
        )

    def add(self, data: Order) -> Order:
        new_order = self.session.add(data)
        self.session.flush()
        return new_order

    def list(self, filter: OrderFilter) -> list[Order]:
        statement = select(Order)

        params = filter.model_dump(exclude_none=True)

        for key, value in params.items():
            statement = statement.where(getattr(Order, key) == value)

        return self.session.scalars(statement).all()

