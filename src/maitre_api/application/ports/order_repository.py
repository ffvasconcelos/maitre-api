import uuid
from typing import Protocol

from sqlalchemy.orm import Session

from maitre_api.application.schemas.order import OrderCreate, OrderFilter, OrderUpdate
from maitre_api.infrastructure.database.models.order import Order


class OrderRepositoryPort(Protocol):
    def __init__(self, session: Session): ...

    def get_by_id(self, id: uuid.UUID) -> Order | None: ...

    def create(self, data: OrderCreate) -> Order: ...

    def list(self, filter: OrderFilter) -> list[Order]: ...

    def update(self, id: uuid.UUID, data: OrderUpdate) -> Order: ...
