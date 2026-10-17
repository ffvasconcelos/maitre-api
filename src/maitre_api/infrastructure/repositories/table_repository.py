import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from maitre_api.application.schemas.table import TableCreate
from maitre_api.domain.enums.table_status import TableStatus
from maitre_api.infrastructure.database.models.table import Table


class TableRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, id: uuid.UUID) -> Table | None:
        return self.session.get(Table, id)

    def get_by_number(self, table_number: int) -> Table | None:
        return self.session.scalar(select(Table).where(
            Table.number == table_number
        ))

    def create(self, data: TableCreate) -> Table:
        new_table = Table(number=data.number, capacity=data.capacity)

        self.session.add(new_table)
        self.session.flush()
        return new_table

    def occupy_table(self, id: uuid.UUID) -> Table:
        table = self.session.get(Table, id)
        table.status = TableStatus.OCCUPIED
        self.session.flush()
        return table

    def free_table(self, id: uuid.UUID) -> Table:
        table = self.session.get(Table, id)
        table.status = TableStatus.AVAIALABLE
        self.session.flush()
        return table

    def list(self) -> list[Table]:
        return self.session.scalars(select(Table).order_by(Table.number.asc())).all()
