from dataclasses import dataclass

from maitre_api.domain.entities.base import Entity
from maitre_api.domain.enums import TableStatus


@dataclass(kw_only=True)
class Table(Entity):
    number: int
    capacity: int
    status: TableStatus = TableStatus.AVAILABLE
