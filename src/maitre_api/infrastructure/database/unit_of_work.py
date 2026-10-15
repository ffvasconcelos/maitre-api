from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session

from maitre_api.application.ports import (
    OrderRepositoryPort,
    ProductRepositoryPort,
    TableRepositoryPort,
)
from maitre_api.infrastructure.repositories import (
    OrderRepository, 
    ProductRepository,
    TableRepository,
)


class SqlAlchemyUnitOfWork:
    def __init__(self, session: Session) -> None:
        self._session = session
        self.products: ProductRepositoryPort = ProductRepository(session)
        self.tables: TableRepositoryPort = TableRepository(session)
        self.orders: OrderRepositoryPort = OrderRepository(session)
        self._committed = False

    def __enter__(self) -> Self:
        self._committed = False
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None or not self._committed:
            self.rollback()

    def commit(self) -> None:
        self._session.commit()
        self._committed = True

    def rollback(self) -> None:
        self._session.rollback()
        self._committed = False
