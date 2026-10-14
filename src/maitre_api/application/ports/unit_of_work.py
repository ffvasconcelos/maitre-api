from types import TracebackType
from typing import Protocol, Self

from maitre_api.application.ports.product_repository import (
    ProductRepositoryPort,
)


class UnitOfWork(Protocol):
    products: ProductRepositoryPort

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
