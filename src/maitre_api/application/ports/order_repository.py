import uuid
from typing import Protocol

from maitre_api.application.schemas.order import OrderFilter
from maitre_api.infrastructure.database.models.order import Order


class OrderRepositoryPort(Protocol):
    def get_by_id(self, id: uuid.UUID) -> Order | None: ...
    
    def get_open_by_table_id(self, table_id: uuid.UUID) -> Order | None: ...
    
    def add(self, data: Order) -> Order: ...
    
    def list(self, filter: OrderFilter) -> list[Order]: ...
