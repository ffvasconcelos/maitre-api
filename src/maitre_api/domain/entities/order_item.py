from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from maitre_api.domain.entities.base import Entity
from maitre_api.domain.entities.product import Product


@dataclass(kw_only=True)
class OrderItem(Entity):
    product: Product
    quantity: int
    unit_price: Decimal

    @property
    def product_id(self) -> UUID:
        return self.product.id
