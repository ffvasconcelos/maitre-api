from dataclasses import dataclass
from decimal import Decimal

from maitre_api.domain.entities.base import Entity


@dataclass(kw_only=True)
class Product(Entity):
    name: str
    price: Decimal
    description: str | None = None
    active: bool = True
