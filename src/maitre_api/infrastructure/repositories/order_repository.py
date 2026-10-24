from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from maitre_api.application.schemas.order import OrderFilter
from maitre_api.domain.enums.order_status import OrderStatus
from maitre_api.infrastructure.database.models.order import Order
from maitre_api.infrastructure.database.models.order_item import OrderItem


class OrderRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, id: UUID, for_update: bool = False) -> Order | None:
        statement = (
            select(Order)
            .options(selectinload(Order.items).joinedload(OrderItem.product))
            .where(Order.id == id)
        )

        if for_update:
            statement = statement.with_for_update().execution_options(
                populate_existing=True
            )

        return self.session.scalars(statement).one_or_none()

    def get_open_by_table_id(
        self, table_id: UUID, for_update: bool = False
    ) -> Order | None:
        statement = select(Order).where(
            Order.table_id == table_id, Order.status == OrderStatus.OPEN
        )

        if for_update:
            statement = statement.with_for_update().execution_options(
                populate_existing=True
            )

        return self.session.scalar(statement)

    def add(self, data: Order) -> Order:
        self.session.add(data)
        self.session.flush()
        return data

    def add_items(self, order: Order, new_items: list[OrderItem]) -> Order:
        order.items.extend(new_items)
        self.session.flush()
        return order

    def list(self, filter: OrderFilter) -> list[Order]:
        statement = select(Order)

        params = filter.model_dump(exclude_none=True)

        for key, value in params.items():
            statement = statement.where(getattr(Order, key) == value)

        return self.session.scalars(statement).all()

    def close(self, order: Order) -> Order:
        order.status = OrderStatus.CLOSED
        self.session.flush()

        return order

    def cancel(self, order: Order) -> Order:
        order.status = OrderStatus.CANCELLED
        self.session.flush()

        return order
