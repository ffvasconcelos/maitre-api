from dataclasses import dataclass, field
from uuid import UUID

from maitre_api.domain.entities.base import Entity
from maitre_api.domain.entities.order_item import OrderItem
from maitre_api.domain.entities.table import Table
from maitre_api.domain.enums import OrderStatus


@dataclass(kw_only=True)
class Order(Entity):
    table: Table
    items: list[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.OPEN

    @property
    def table_id(self) -> UUID:
        return self.table.id
