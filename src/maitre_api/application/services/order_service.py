from uuid import UUID

from maitre_api.application.ports.unit_of_work import UnitOfWork
from maitre_api.application.schemas.order import OrderCreate, OrderFilter, OrderUpdate
from maitre_api.domain.enums import OrderStatus, TableStatus
from maitre_api.domain.exceptions.order import OrderDoesNotExists, OrderNotOpen
from maitre_api.domain.exceptions.table import TableNotAvaiable
from maitre_api.infrastructure.database.models.order import Order


class OrderService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def create_order(self, order_create: OrderCreate) -> Order:
        with self._uow as uow:
            table = uow.tables.get_by_id(order_create.table_id)

            if table.status != TableStatus.AVAIALABLE:
                raise TableNotAvaiable(table.number)

            order = uow.orders.create(order_create)
            uow.commit()
            return order

    def get_order_by_id(self, order_id: UUID) -> Order | None:
        with self._uow as uow:
            return uow.orders.get_by_id(order_id)

    def list_orders(self, filter: OrderFilter) -> list[Order]:
        with self._uow as uow:
            return uow.orders.list(filter)

    # Placeholder to function. Will be developed with base items module
    def add_item(self, id: UUID, item: dict) -> None:
        pass

    def close_order(self, id: UUID) -> Order:
        with self._uow as uow:
            order = uow.orders.get_by_id(id)

            if order is None:
                raise OrderDoesNotExists(id)
            elif order.status != OrderStatus.OPEN:
                raise OrderNotOpen(id)

            closed_order = uow.orders.update(id, OrderUpdate(status=OrderStatus.CLOSED))
            return closed_order

    def cancel_order(self) -> Order:
        with self._uow as uow:
            order = uow.orders.get_by_id(id)

            if order is None:
                raise OrderDoesNotExists(id)
            elif order.status != OrderStatus.OPEN:
                raise OrderNotOpen(id)

            closed_order = uow.orders.update(
                id, OrderUpdate(status=OrderStatus.CANCELLED)
            )
            return closed_order
