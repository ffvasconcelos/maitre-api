import uuid
from typing import Protocol

from maitre_api.application.schemas.table import TableCreate
from maitre_api.domain.entities.table import Table


class TableRepositoryPort(Protocol):
    def get_by_id(self, id: uuid.UUID, for_update: bool = False) -> Table | None: ...

    def get_by_number(
        self, table_number: int, for_update: bool = False
    ) -> Table | None: ...

    def create(self, data: TableCreate) -> Table: ...

    def occupy_table(self, table: Table) -> Table: ...

    def free_table(self, table: Table) -> Table: ...

    def list(self) -> list[Table]: ...
