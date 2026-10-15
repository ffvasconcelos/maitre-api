import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from maitre_api.application.schemas.order import OrderCreate, OrderFilter, OrderUpdate
from maitre_api.infrastructure.database.models.order import Order


class OrderRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, id: uuid.UUID) -> Order | None:
        return self.session.get(Order, id)

    def create(self, data: OrderCreate) -> Order:
        new_order = Order(table_id=data.table_id)

        self.session.add(new_order)
        self.session.flush()
        return new_order

    def list(self, filter: OrderFilter) -> list[Order]:
        statement = select(Order)

        params = filter.model_dump(exclude_none=True)

        for key, value in params.items():
            statement = statement.where(getattr(Order, key) == value)
        
        return self.session.scalars(statement).all()

    def update(self, id: uuid.UUID, data: OrderUpdate) -> Order:
        order = self.get_by_id(Order, id)

        if order is None:
            return None

        changes = data.model_dump(exclude_unset=True)

        for key, value in changes.items():
            setattr(order, key, value)

        self.session.flush()
        return order
        
