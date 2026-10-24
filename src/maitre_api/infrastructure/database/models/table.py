from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Integer
from sqlalchemy import Enum as SqlAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column

from maitre_api.domain.enums import TableStatus
from maitre_api.infrastructure.database.base import BaseModel


class Table(BaseModel):
    __tablename__ = "tables"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    number: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint("number > 0", name="check_table_number_gt_0"),
        nullable=False,
        unique=True,
    )
    capacity: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint("capacity > 0", name="check_capacity_number_gt_0"),
        nullable=False,
        default=2,
    )
    status: Mapped[TableStatus] = mapped_column(
        SqlAlchemyEnum(TableStatus, name="table_status"), default=TableStatus.AVAIALABLE
    )
