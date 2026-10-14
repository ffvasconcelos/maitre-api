from uuid import UUID

from maitre_api.application.ports.unit_of_work import UnitOfWork
from maitre_api.application.schemas.table import TableCreate
from maitre_api.infrastructure.database.models.table import Table


class TableService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def create_table(self, table_create: TableCreate) -> Table:
        with self._uow as uow:
            table = uow.tables.create(table_create)
            uow.commit()
            return table

    def get_table_by_id(self, table_id: UUID) -> Table | None:
        with self._uow as uow:
            return uow.tables.get_by_id(table_id)

    def get_table_by_number(self, table_number: int) -> Table | None:
        with self._uow as uow:
            return uow.tables.get_by_number(table_number)

    def list_tables(self) -> list[Table]:
        with self._uow as uow:
            return uow.tables.list()

