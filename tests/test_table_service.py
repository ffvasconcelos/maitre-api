from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from maitre_api.application.schemas.table import TableCreate
from maitre_api.application.services.table_service import TableService
from maitre_api.domain.exceptions.table import (
    TableNotFound,
    TableNumberAlreadyExists,
    TableNumberNotFound,
)
from maitre_api.infrastructure.database.models.table import Table


def make_service() -> tuple[TableService, MagicMock]:
    uow = MagicMock()
    uow.__enter__.return_value = uow
    return TableService(uow), uow


def test_create_table_rejects_duplicate_number() -> None:
    service, uow = make_service()
    uow.tables.get_by_number.return_value = Table(number=3, capacity=4)

    with pytest.raises(TableNumberAlreadyExists):
        service.create_table(TableCreate(number=3, capacity=4))

    uow.tables.create.assert_not_called()
    uow.commit.assert_not_called()


def test_create_table_persists_and_commits() -> None:
    service, uow = make_service()
    table_data = TableCreate(number=3, capacity=4)
    table = Table(number=3, capacity=4)
    uow.tables.get_by_number.return_value = None
    uow.tables.create.return_value = table

    result = service.create_table(table_data)

    assert result is table
    uow.tables.get_by_number.assert_called_once_with(3)
    uow.tables.create.assert_called_once_with(table_data)
    uow.commit.assert_called_once_with()


def test_get_table_by_id_raises_for_missing_table() -> None:
    service, uow = make_service()
    table_id = uuid4()
    uow.tables.get_by_id.return_value = None

    with pytest.raises(TableNotFound):
        service.get_table_by_id(table_id)


def test_get_table_by_number_raises_for_missing_table() -> None:
    service, uow = make_service()
    uow.tables.get_by_number.return_value = None

    with pytest.raises(TableNumberNotFound):
        service.get_table_by_number(42)


def test_get_and_list_tables_return_repository_results() -> None:
    service, uow = make_service()
    table = Table(number=3, capacity=4)
    tables = [table]
    uow.tables.get_by_id.return_value = table
    uow.tables.get_by_number.return_value = table
    uow.tables.list.return_value = tables

    assert service.get_table_by_id(table.id) is table
    assert service.get_table_by_number(3) is table
    assert service.list_tables() is tables
    uow.commit.assert_not_called()