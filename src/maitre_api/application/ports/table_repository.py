import uuid
from typing import Protocol

from maitre_api.application.schemas.table import TableCreate
from maitre_api.infrastructure.database.models.table import Table


class TableRepositoryPort(Protocol):
    def get_by_id(self, id: uuid.UUID) -> Table | None: ...

    def get_by_number(self, table_number: int) -> Table | None: ...

    def create(self, data: TableCreate) -> Table: ...

    def list(self) -> list[Table]: ...
