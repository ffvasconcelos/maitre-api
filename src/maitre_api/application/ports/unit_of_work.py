from types import TracebackType
from typing import Protocol, Self

from maitre_api.application.ports import (
    OrderRepositoryPort,
    ProductRepositoryPort,
    TableRepositoryPort,
)


class UnitOfWork(Protocol):
    products: ProductRepositoryPort
    tables: TableRepositoryPort
    orders: OrderRepositoryPort

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
