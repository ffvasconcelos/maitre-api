from uuid import UUID

from psycopg.errors import UniqueViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from maitre_api.application.schemas.table import TableCreate
from maitre_api.domain.entities.table import Table
from maitre_api.domain.enums.table_status import TableStatus
from maitre_api.domain.exceptions.table import TableNumberAlreadyExists
from maitre_api.infrastructure.database.models.table import Table as TableModel
from maitre_api.infrastructure.repositories.mappers import to_table, update_timestamps


class TableRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, id: UUID, for_update: bool = False) -> Table | None:
        statement = select(TableModel).where(TableModel.id == id)
        if for_update:
            statement = statement.with_for_update().execution_options(
                populate_existing=True
            )
        model = self.session.scalar(statement)
        return to_table(model) if model is not None else None

    def get_by_number(
        self, table_number: int, for_update: bool = False
    ) -> Table | None:
        statement = select(TableModel).where(TableModel.number == table_number)

        if for_update:
            statement = statement.with_for_update().execution_options(
                populate_existing=True
            )
        model = self.session.scalar(statement)
        return to_table(model) if model is not None else None

    def create(self, data: TableCreate) -> Table:
        new_table = TableModel(number=data.number, capacity=data.capacity)

        self.session.add(new_table)
        try:
            self.session.flush()
        except IntegrityError as exc:
            if (
                isinstance(exc.orig, UniqueViolation)
                and exc.orig.diag.constraint_name == "tables_number_key"
            ):
                raise TableNumberAlreadyExists(data.number) from exc
            raise
        return to_table(new_table)

    def occupy_table(self, table: Table) -> Table:
        return self._set_status(table, TableStatus.OCCUPIED)

    def free_table(self, table: Table) -> Table:
        return self._set_status(table, TableStatus.AVAILABLE)

    def list(self) -> list[Table]:
        statement = select(TableModel).order_by(TableModel.number.asc())
        return [to_table(model) for model in self.session.scalars(statement).all()]

    def _set_status(self, table: Table, status: TableStatus) -> Table:
        model = self.session.get(TableModel, table.id)
        model.status = status
        self.session.flush()
        table.status = model.status
        update_timestamps(table, model)
        return table
