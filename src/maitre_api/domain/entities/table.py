from dataclasses import dataclass

from maitre_api.domain.entities.base import Entity
from maitre_api.domain.enums import TableStatus
from maitre_api.domain.exceptions.table import TableNotAvailable


@dataclass(kw_only=True)
class Table(Entity):
    number: int
    capacity: int
    status: TableStatus = TableStatus.AVAILABLE

    def occupy(self) -> None:
        if self.status != TableStatus.AVAILABLE:
            raise TableNotAvailable(self.number)
        self.status = TableStatus.OCCUPIED

    def release(self) -> None:
        self.status = TableStatus.AVAILABLE
