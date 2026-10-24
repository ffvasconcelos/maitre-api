from dataclasses import dataclass, field
from uuid import UUID

from maitre_api.domain.entities.base import Entity
from maitre_api.domain.entities.order_item import OrderItem
from maitre_api.domain.entities.table import Table
from maitre_api.domain.enums import OrderStatus
from maitre_api.domain.exceptions.order import OrderNotOpen


@dataclass(kw_only=True)
class Order(Entity):
    table: Table
    items: list[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.OPEN

    @property
    def table_id(self) -> UUID:
        return self.table.id

    def ensure_open(self) -> None:
        if self.status != OrderStatus.OPEN:
            raise OrderNotOpen(self.id)

    def add_items(self, items: list[OrderItem]) -> None:
        self.ensure_open()
        self.items.extend(items)

    def close(self) -> None:
        self.ensure_open()
        self.status = OrderStatus.CLOSED

    def cancel(self) -> None:
        self.ensure_open()
        self.status = OrderStatus.CANCELLED
