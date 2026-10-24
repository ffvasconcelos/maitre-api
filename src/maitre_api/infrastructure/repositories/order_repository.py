from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from maitre_api.application.schemas.order import OrderFilter
from maitre_api.domain.entities.order import Order
from maitre_api.domain.entities.order_item import OrderItem
from maitre_api.domain.enums.order_status import OrderStatus
from maitre_api.infrastructure.database.models.order import Order as OrderModel
from maitre_api.infrastructure.database.models.order_item import (
    OrderItem as OrderItemModel,
)
from maitre_api.infrastructure.repositories.mappers import (
    to_order,
    to_order_item_model,
    update_timestamps,
)


class OrderRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, id: UUID, for_update: bool = False) -> Order | None:
        statement = (
            select(OrderModel)
            .options(
                selectinload(OrderModel.table),
                selectinload(OrderModel.items).joinedload(OrderItemModel.product),
            )
            .where(OrderModel.id == id)
        )

        if for_update:
            statement = statement.with_for_update().execution_options(
                populate_existing=True
            )

        model = self.session.scalars(statement).one_or_none()
        return to_order(model) if model is not None else None

    def get_open_by_table_id(
        self, table_id: UUID, for_update: bool = False
    ) -> Order | None:
        statement = (
            select(OrderModel)
            .options(
                selectinload(OrderModel.table),
                selectinload(OrderModel.items).joinedload(OrderItemModel.product),
            )
            .where(
                OrderModel.table_id == table_id, OrderModel.status == OrderStatus.OPEN
            )
        )

        if for_update:
            statement = statement.with_for_update().execution_options(
                populate_existing=True
            )

        model = self.session.scalar(statement)
        return to_order(model) if model is not None else None

    def add(self, data: Order) -> Order:
        model = OrderModel(
            id=data.id,
            table_id=data.table_id,
            status=data.status,
            items=[to_order_item_model(item) for item in data.items],
        )
        self.session.add(model)
        self.session.flush()
        update_timestamps(data, model)
        for item, item_model in zip(data.items, model.items, strict=True):
            update_timestamps(item, item_model)
        return data

    def add_items(self, order: Order, new_items: list[OrderItem]) -> Order:
        model = self.session.get(OrderModel, order.id)
        models = [to_order_item_model(item) for item in new_items]
        model.items.extend(models)
        self.session.flush()
        for item, item_model in zip(new_items, models, strict=True):
            update_timestamps(item, item_model)
        order.items.extend(new_items)
        return order

    def list(self, filter: OrderFilter) -> list[Order]:
        statement = select(OrderModel).options(
            selectinload(OrderModel.table),
            selectinload(OrderModel.items).joinedload(OrderItemModel.product),
        )

        params = filter.model_dump(exclude_none=True)

        for key, value in params.items():
            statement = statement.where(getattr(OrderModel, key) == value)

        return [to_order(model) for model in self.session.scalars(statement).all()]

    def close(self, order: Order) -> Order:
        return self._set_status(order, OrderStatus.CLOSED)

    def cancel(self, order: Order) -> Order:
        return self._set_status(order, OrderStatus.CANCELLED)

    def _set_status(self, order: Order, status: OrderStatus) -> Order:
        model = self.session.get(OrderModel, order.id)
        model.status = status
        self.session.flush()
        order.status = model.status
        update_timestamps(order, model)
        return order
