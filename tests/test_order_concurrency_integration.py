from concurrent.futures import ThreadPoolExecutor
from threading import Event
from time import sleep
from uuid import uuid4

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from maitre_api.application.schemas.order import OrderCreate
from maitre_api.application.services.order_service import OrderService
from maitre_api.domain.enums import OrderStatus
from maitre_api.domain.exceptions.table import TableNotAvaiable
from maitre_api.infrastructure.database.models.order import Order
from maitre_api.infrastructure.database.models.table import Table
from maitre_api.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def create_table(session_factory: sessionmaker[Session]) -> Table:
    with session_factory() as session:
        table = Table(number=uuid4().int % 1_000_000 + 1, capacity=4)
        session.add(table)
        session.commit()
        return table


def test_open_order_index_rejects_duplicate_open_orders(
    integration_session_factory: sessionmaker[Session],
) -> None:
    table = create_table(integration_session_factory)

    with integration_session_factory() as session:
        session.add(Order(table_id=table.id, status=OrderStatus.OPEN))
        session.commit()

        session.add(Order(table_id=table.id, status=OrderStatus.OPEN))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        session.add(Order(table_id=table.id, status=OrderStatus.CLOSED))
        session.commit()
        session.add(Order(table_id=table.id, status=OrderStatus.CANCELLED))
        session.commit()


def test_table_lock_allows_only_one_concurrent_order(
    integration_session_factory: sessionmaker[Session],
) -> None:
    table = create_table(integration_session_factory)
    first_order_waiting_to_commit = Event()
    allow_first_order_commit = Event()
    second_order_started = Event()

    def create_first_order() -> None:
        session = integration_session_factory()

        def hold_transaction_before_commit(_: Session) -> None:
            first_order_waiting_to_commit.set()
            assert allow_first_order_commit.wait(timeout=5)

        event.listen(
            session, "before_commit", hold_transaction_before_commit, once=True
        )
        try:
            OrderService(SqlAlchemyUnitOfWork(session)).create_order(
                OrderCreate(table_id=table.id, items=[])
            )
        finally:
            session.close()

    def create_second_order() -> None:
        second_order_started.set()
        with integration_session_factory() as session:
            OrderService(SqlAlchemyUnitOfWork(session)).create_order(
                OrderCreate(table_id=table.id, items=[])
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_order = executor.submit(create_first_order)
        assert first_order_waiting_to_commit.wait(timeout=5)

        second_order = executor.submit(create_second_order)
        assert second_order_started.wait(timeout=5)
        sleep(0.2)
        assert not second_order.done()

        allow_first_order_commit.set()
        first_order.result(timeout=5)
        with pytest.raises(TableNotAvaiable):
            second_order.result(timeout=5)

    with integration_session_factory() as session:
        assert (
            session.scalar(
                select(func.count())
                .select_from(Order)
                .where(Order.table_id == table.id)
            )
            == 1
        )
