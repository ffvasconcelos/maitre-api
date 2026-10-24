from uuid import UUID

from psycopg.errors import UniqueViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from maitre_api.application.schemas.table import TableCreate
from maitre_api.domain.enums.table_status import TableStatus
from maitre_api.domain.exceptions.table import TableNumberAlreadyExists
from maitre_api.infrastructure.database.models.table import Table


class TableRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, id: UUID, for_update: bool = False) -> Table | None:
        statement = select(Table).where(Table.id == id)
        if for_update:
            statement = statement.with_for_update().execution_options(
                populate_existing=True
            )
        return self.session.scalar(statement)

    def get_by_number(
        self, table_number: int, for_update: bool = False
    ) -> Table | None:
        statement = select(Table).where(Table.number == table_number)

        if for_update:
            statement = statement.with_for_update().execution_options(
                populate_existing=True
            )
        return self.session.scalar(statement)

    def create(self, data: TableCreate) -> Table:
        new_table = Table(number=data.number, capacity=data.capacity)

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
        return new_table

    def occupy_table(self, table: Table) -> Table:
        table.status = TableStatus.OCCUPIED
        self.session.flush()
        return table

    def free_table(self, table: Table) -> Table:
        table.status = TableStatus.AVAIALABLE
        self.session.flush()
        return table

    def list(self) -> list[Table]:
        return self.session.scalars(select(Table).order_by(Table.number.asc())).all()
