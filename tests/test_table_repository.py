from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from psycopg.errors import CheckViolation, UniqueViolation
from psycopg.pq import DiagnosticField
from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from maitre_api.application.schemas.table import TableCreate
from maitre_api.domain.entities.table import Table as TableEntity
from maitre_api.domain.enums import TableStatus
from maitre_api.domain.exceptions.table import TableNumberAlreadyExists
from maitre_api.infrastructure.database.models.table import Table
from maitre_api.infrastructure.repositories.table_repository import TableRepository


def make_repository() -> tuple[TableRepository, MagicMock]:
    session = MagicMock(spec=Session)
    return TableRepository(session), session


@pytest.mark.parametrize("for_update", [False, True])
@pytest.mark.parametrize("found", [False, True])
def test_get_by_id_queries_matching_table(for_update: bool, found: bool) -> None:
    repository, session = make_repository()
    table_id = uuid4()
    table = Table(number=2, capacity=4) if found else None
    session.scalar.return_value = table

    result = repository.get_by_id(table_id, for_update=for_update)
    if found:
        assert isinstance(result, TableEntity)
        assert result.number == table.number
        assert result.capacity == table.capacity
    else:
        assert result is None

    session.scalar.assert_called_once()
    statement = session.scalar.call_args.args[0]
    compiled = statement.compile(dialect=postgresql.dialect())
    assert "WHERE tables.id = %(id_1)s" in str(compiled)
    assert compiled.params["id_1"] == table_id
    assert ("FOR UPDATE" in str(compiled)) is for_update


@pytest.mark.parametrize("for_update", [False, True])
@pytest.mark.parametrize("found", [False, True])
def test_get_by_number_queries_matching_number(for_update: bool, found: bool) -> None:
    repository, session = make_repository()
    table = Table(number=2, capacity=4) if found else None
    session.scalar.return_value = table

    result = repository.get_by_number(2, for_update=for_update)
    if found:
        assert isinstance(result, TableEntity)
        assert result.number == table.number
        assert result.capacity == table.capacity
    else:
        assert result is None

    session.scalar.assert_called_once()
    statement = session.scalar.call_args.args[0]
    compiled = statement.compile(dialect=postgresql.dialect())
    assert "tables.number = %(number_1)s" in str(compiled)
    assert compiled.params["number_1"] == 2
    assert ("FOR UPDATE" in str(compiled)) is for_update


@pytest.mark.parametrize("lookup", ["get_by_id", "get_by_number"])
def test_get_does_not_lock_by_default(lookup: str) -> None:
    repository, session = make_repository()
    key = uuid4() if lookup == "get_by_id" else 2

    getattr(repository, lookup)(key)

    statement = session.scalar.call_args.args[0]
    assert "FOR UPDATE" not in str(statement.compile(dialect=postgresql.dialect()))


def test_create_adds_and_flushes_table() -> None:
    repository, session = make_repository()
    table_data = TableCreate(number=2, capacity=4)

    result = repository.create(table_data)

    assert result.number == 2
    assert result.capacity == 4
    assert isinstance(result, TableEntity)
    model = session.add.call_args.args[0]
    assert isinstance(model, Table)
    assert model.number == result.number
    assert model.capacity == result.capacity
    session.flush.assert_called_once_with()


def test_create_translates_duplicate_table_number() -> None:
    repository, session = make_repository()
    original = UniqueViolation(
        "duplicate table number",
        info={DiagnosticField.CONSTRAINT_NAME: b"tables_number_key"},
    )
    error = IntegrityError("INSERT INTO tables", {}, original)
    session.flush.side_effect = error

    with pytest.raises(TableNumberAlreadyExists) as raised:
        repository.create(TableCreate(number=2, capacity=4))

    assert raised.value.number == 2
    assert raised.value.__cause__ is error


@pytest.mark.parametrize(
    "original",
    [
        UniqueViolation(
            "duplicate primary key",
            info={DiagnosticField.CONSTRAINT_NAME: b"tables_pkey"},
        ),
        CheckViolation(
            "different integrity failure",
            info={DiagnosticField.CONSTRAINT_NAME: b"tables_number_key"},
        ),
        RuntimeError("missing database diagnostics"),
    ],
)
def test_create_preserves_unrelated_integrity_errors(original: Exception) -> None:
    repository, session = make_repository()
    error = IntegrityError("INSERT INTO tables", {}, original)
    session.flush.side_effect = error

    with pytest.raises(IntegrityError) as raised:
        repository.create(TableCreate(number=2, capacity=4))

    assert raised.value is error


@pytest.mark.parametrize("status", list(TableStatus))
def test_save_status_persists_the_domain_status(status: TableStatus) -> None:
    repository, session = make_repository()
    table = TableEntity(number=2, capacity=4, status=status)
    model = Table(id=table.id, number=2, capacity=4)
    session.get.return_value = model

    assert repository.save_status(table) is table
    assert model.status == status
    session.get.assert_called_once_with(Table, table.id)
    session.flush.assert_called_once_with()


def test_list_orders_tables_by_number_ascending() -> None:
    repository, session = make_repository()
    tables = [Table(number=1, capacity=2)]
    session.scalars.return_value.all.return_value = tables

    result = repository.list()
    assert len(result) == 1
    assert isinstance(result[0], TableEntity)
    assert result[0].number == tables[0].number
    assert str(session.scalars.call_args.args[0]) == str(
        select(Table).order_by(Table.number.asc())
    )
