from uuid import UUID

from maitre_api.application.ports.unit_of_work import UnitOfWork
from maitre_api.application.schemas.order import (
    OrderCreate,
    OrderFilter,
    OrderItemCreate,
)
from maitre_api.domain.enums import TableStatus
from maitre_api.domain.enums.order_status import OrderStatus
from maitre_api.domain.exceptions.order import OrderDoesNotExists, OrderNotOpen
from maitre_api.domain.exceptions.product import ProductNotActive, ProductNotFound
from maitre_api.domain.exceptions.table import TableNotAvaiable, TableNotFound
from maitre_api.infrastructure.database.models.order import Order
from maitre_api.infrastructure.database.models.order_item import OrderItem


class OrderService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def create_order(self, order_create: OrderCreate) -> Order:
        with self._uow as uow:
            table = uow.tables.get_by_id(order_create.table_id)

            if table is None:
                raise TableNotFound(order_create.table_id)
            if table.status != TableStatus.AVAIALABLE:
                raise TableNotAvaiable(table.number)

            uow.tables.occupy_table(order_create.table_id)

            order = uow.orders.add(
                Order(
                    table_id=order_create.table_id,
                    items=self._assemble_items(uow, order_create.items),
                )
            )
            uow.commit()
            return order

    def get_order_by_id(self, order_id: UUID) -> Order | None:
        with self._uow as uow:
            order = uow.orders.get_by_id(order_id)

            if order is None:
                raise OrderDoesNotExists(order_id)

            return order

    def add_order_items(
        self, order_id: UUID, order_items: list[OrderItemCreate]
    ) -> Order:
        with self._uow as uow:
            order = uow.orders.get_by_id(order_id)

            if order is None:
                raise OrderDoesNotExists(order_id)
            elif order.status != OrderStatus.OPEN:
                raise OrderNotOpen(order_id)

            items = self._assemble_items(uow, order_items)
            updated_order = uow.orders.add_items(order, items)
            uow.commit()

            return updated_order

    def list_orders(self, filter: OrderFilter) -> list[Order]:
        with self._uow as uow:
            return uow.orders.list(filter)

    # Private functions
    def _assemble_items(
        self, uow: UnitOfWork, order_items: list[OrderItemCreate]
    ) -> list[OrderItem]:
        items = []

        for item in order_items:
            product = uow.products.get_by_id(item.product_id)

            if product is None:
                raise ProductNotFound(item.product_id)
            elif not product.active:
                raise ProductNotActive(item.product_id)

            items.append(
                OrderItem(
                    product=product, quantity=item.quantity, unit_price=product.price
                )
            )

        return items
