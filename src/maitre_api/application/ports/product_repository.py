from typing import Protocol
from uuid import UUID

from maitre_api.application.schemas.product import ProductCreate
from maitre_api.domain.entities.product import Product


class ProductRepositoryPort(Protocol):
    def create(self, product_data: ProductCreate) -> Product: ...

    def get_by_id(self, product_id: UUID) -> Product | None: ...

    def list(self) -> list[Product]: ...
