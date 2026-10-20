from unittest.mock import MagicMock
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from maitre_api.application.schemas.table import TableCreate
from maitre_api.domain.enums import TableStatus
from maitre_api.infrastructure.database.models.table import Table
from maitre_api.infrastructure.repositories.table_repository import TableRepository


def make_repository() -> tuple[TableRepository, MagicMock]:
    session = MagicMock(spec=Session)
    return TableRepository(session), session


def test_get_by_id_uses_session_lookup() -> None:
    repository, session = make_repository()
    table_id = uuid4()
    table = Table(number=2, capacity=4)
    session.get.return_value = table

    assert repository.get_by_id(table_id) is table
    session.get.assert_called_once_with(Table, table_id)


def test_get_by_id_for_update_locks_matching_table() -> None:
    repository, session = make_repository()
    table_id = uuid4()
    table = Table(number=2, capacity=4)
    session.scalar.return_value = table

    assert repository.get_by_id_for_update(table_id) is table

    statement = session.scalar.call_args.args[0]
    compiled = str(statement.compile(dialect=postgresql.dialect()))
    assert "WHERE tables.id = %(id_1)s" in compiled
    assert compiled.endswith("FOR UPDATE")


def test_get_by_number_queries_matching_number() -> None:
    repository, session = make_repository()
    table = Table(number=2, capacity=4)
    session.scalar.return_value = table

    assert repository.get_by_number(2) is table
    statement = session.scalar.call_args.args[0]
    assert "tables.number = :number_1" in str(statement)


def test_create_adds_and_flushes_table() -> None:
    repository, session = make_repository()
    table_data = TableCreate(number=2, capacity=4)

    result = repository.create(table_data)

    assert result.number == 2
    assert result.capacity == 4
    session.add.assert_called_once_with(result)
    session.flush.assert_called_once_with()


def test_occupy_and_free_update_table_status() -> None:
    repository, session = make_repository()
    table_id = uuid4()
    table = Table(number=2, capacity=4)
    session.get.return_value = table

    assert repository.occupy_table(table_id) is table
    assert table.status == TableStatus.OCCUPIED
    assert repository.free_table(table) is table
    assert table.status == TableStatus.AVAIALABLE
    session.get.assert_called_once_with(Table, table_id)
    assert session.flush.call_count == 2


def test_list_orders_tables_by_number_ascending() -> None:
    repository, session = make_repository()
    tables = [Table(number=1, capacity=2)]
    session.scalars.return_value.all.return_value = tables

    assert repository.list() is tables
    assert str(session.scalars.call_args.args[0]) == str(
        select(Table).order_by(Table.number.asc())
    )
