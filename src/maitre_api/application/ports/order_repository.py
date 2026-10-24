import uuid
from typing import Protocol

from maitre_api.application.schemas.order import OrderFilter
from maitre_api.domain.entities.order import Order
from maitre_api.domain.entities.order_item import OrderItem


class OrderRepositoryPort(Protocol):
    def get_by_id(self, id: uuid.UUID, for_update: bool = False) -> Order | None: ...

    def get_open_by_table_id(
        self, table_id: uuid.UUID, for_update: bool = False
    ) -> Order | None: ...

    def add(self, data: Order) -> Order: ...

    def add_items(self, order: Order, new_items: list[OrderItem]) -> Order: ...

    def list(self, filter: OrderFilter) -> list[Order]: ...

    def save_status(self, order: Order) -> Order: ...
