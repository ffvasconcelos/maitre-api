from itertools import count

import pytest
from sqlalchemy.orm import Session, sessionmaker

from maitre_api.application.schemas.order import OrderCreate
from maitre_api.application.schemas.table import TableCreate
from maitre_api.application.services.order_service import OrderService
from maitre_api.domain.enums import TableStatus
from maitre_api.domain.exceptions.table import (
    TableNotAvaiable,
    TableNumberAlreadyExists,
)
from maitre_api.infrastructure.database.models.table import Table
from maitre_api.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from maitre_api.infrastructure.repositories.table_repository import TableRepository

table_numbers = count(200_000_000)


@pytest.mark.parametrize("lookup", ["get_by_id", "get_by_number"])
def test_locked_read_refreshes_preloaded_table_status(
    integration_session_factory: sessionmaker[Session], lookup: str
) -> None:
    factory = integration_session_factory
    with factory() as session:
        table = Table(number=next(table_numbers), capacity=4)
        session.add(table)
        session.commit()
        table_id, table_number = table.id, table.number

    key = table_id if lookup == "get_by_id" else table_number
    with factory() as stale_session:
        cached_model = stale_session.get(Table, table_id)
        assert cached_model.status == TableStatus.AVAIALABLE
        repository = TableRepository(stale_session)
        cached_table = getattr(repository, lookup)(key)
        assert cached_table.status == TableStatus.AVAIALABLE

        with factory() as session:
            OrderService(SqlAlchemyUnitOfWork(session)).create_order(
                OrderCreate(table_id=table_id, items=[])
            )

        refreshed = getattr(repository, lookup)(key, for_update=True)
        assert refreshed.status == TableStatus.OCCUPIED
        assert cached_model.status == TableStatus.OCCUPIED
        assert refreshed.id == table_id
        assert refreshed.number == table_number

        with pytest.raises(TableNotAvaiable):
            OrderService(SqlAlchemyUnitOfWork(stale_session)).create_order(
                OrderCreate(table_id=table_id, items=[])
            )


def test_duplicate_table_rolls_back_and_session_remains_usable(
    integration_session_factory: sessionmaker[Session],
) -> None:
    number = next(table_numbers)
    with integration_session_factory() as session:
        with SqlAlchemyUnitOfWork(session) as uow:
            uow.tables.create(TableCreate(number=number, capacity=4))
            uow.commit()

        with pytest.raises(TableNumberAlreadyExists):
            with SqlAlchemyUnitOfWork(session) as uow:
                uow.tables.create(TableCreate(number=number, capacity=4))

        # Keep the session open to verify rollback, rather than relying on close().
        assert session.is_active
        assert not session.in_transaction()
        with SqlAlchemyUnitOfWork(session) as uow:
            original = uow.tables.get_by_number(number)
            assert original is not None
            created = uow.tables.create(
                TableCreate(number=next(table_numbers), capacity=4)
            )
            uow.commit()

        assert created.id != original.id
