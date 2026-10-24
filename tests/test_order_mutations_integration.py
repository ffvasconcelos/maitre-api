from concurrent.futures import Future, ThreadPoolExecutor
from decimal import Decimal
from itertools import count
from threading import Event
from time import monotonic
from uuid import UUID

import pytest
from sqlalchemy import event, func, select, text
from sqlalchemy.orm import Session, sessionmaker

from maitre_api.application.schemas.order import OrderCreate, OrderItemCreate
from maitre_api.application.services.order_service import OrderService
from maitre_api.domain.enums import OrderStatus, TableStatus
from maitre_api.domain.exceptions.order import OrderNotOpen
from maitre_api.infrastructure.database.models.order import Order
from maitre_api.infrastructure.database.models.product import Product
from maitre_api.infrastructure.database.models.table import Table
from maitre_api.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from maitre_api.infrastructure.repositories.order_repository import OrderRepository

table_numbers = count(100_000_000)
mutations = ["close_order", "cancel_order", "add_order_items"]


@pytest.fixture
def order_context(
    integration_session_factory: sessionmaker[Session],
) -> tuple[UUID, UUID, UUID]:
    with integration_session_factory() as session:
        table = Table(number=next(table_numbers), capacity=4)
        product = Product(name="Soup", price=Decimal("9.50"), active=True)
        session.add_all([table, product])
        session.commit()
        order = OrderService(SqlAlchemyUnitOfWork(session)).create_order(
            OrderCreate(table_id=table.id, items=[])
        )
        return table.id, order.id, product.id


def mutate(session: Session, operation: str, order_id: UUID, product_id: UUID) -> Order:
    service = OrderService(SqlAlchemyUnitOfWork(session))
    if operation == "add_order_items":
        return service.add_order_items(
            order_id, [OrderItemCreate(product_id=product_id, quantity=2)]
        )
    return getattr(service, operation)(order_id)


def assert_waiting_for_lock(factory: sessionmaker[Session], pid: int) -> None:
    deadline = monotonic() + 3
    pause = Event()
    with factory() as observer:
        while monotonic() < deadline:
            if observer.scalar(select(func.cardinality(func.pg_blocking_pids(pid)))):
                return
            pause.wait(0.01)
    pytest.fail("The competing operation did not wait for the database lock")


@pytest.mark.parametrize("first_operation", mutations)
@pytest.mark.parametrize("second_operation", mutations)
def test_concurrent_mutations_preserve_order_and_table_state(
    integration_session_factory: sessionmaker[Session],
    order_context: tuple[UUID, UUID, UUID],
    first_operation: str,
    second_operation: str,
) -> None:
    factory = integration_session_factory
    table_id, order_id, product_id = order_context
    first_waiting = Event()
    release_first = Event()
    second_pid: Future[int] = Future()

    def first_mutation() -> None:
        with factory() as session:

            def hold_commit(_: Session) -> None:
                first_waiting.set()
                assert release_first.wait(timeout=10)

            event.listen(session, "before_commit", hold_commit, once=True)
            mutate(session, first_operation, order_id, product_id)

    def second_mutation() -> None:
        with factory() as session:
            session.execute(text("SET LOCAL lock_timeout = '5s'"))
            second_pid.set_result(session.scalar(select(func.pg_backend_pid())))
            mutate(session, second_operation, order_id, product_id)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(first_mutation)
        try:
            assert first_waiting.wait(timeout=5)
            second = executor.submit(second_mutation)
            assert_waiting_for_lock(factory, second_pid.result(timeout=5))
        finally:
            release_first.set()
        first.result(timeout=5)
        if first_operation == "add_order_items":
            second.result(timeout=5)
        else:
            with pytest.raises(OrderNotOpen):
                second.result(timeout=5)

    terminal_operation = (
        second_operation if first_operation == "add_order_items" else first_operation
    )
    expected_status = {
        "close_order": OrderStatus.CLOSED,
        "cancel_order": OrderStatus.CANCELLED,
        "add_order_items": OrderStatus.OPEN,
    }[terminal_operation]
    expected_item_count = int(first_operation == "add_order_items")
    if first_operation == "add_order_items":
        expected_item_count += int(second_operation == "add_order_items")

    with factory() as session:
        order = OrderRepository(session).get_by_id(order_id)
        assert order.status == expected_status
        assert len(order.items) == expected_item_count
        assert all(item.quantity == 2 for item in order.items)
        assert all(item.unit_price == Decimal("9.50") for item in order.items)
        assert session.get(Table, table_id).status == (
            TableStatus.OCCUPIED
            if expected_status == OrderStatus.OPEN
            else TableStatus.AVAIALABLE
        )


@pytest.mark.parametrize("operation", mutations)
def test_preloaded_order_cannot_change_a_reoccupied_table(
    integration_session_factory: sessionmaker[Session],
    order_context: tuple[UUID, UUID, UUID],
    operation: str,
) -> None:
    factory = integration_session_factory
    table_id, order_id, product_id = order_context
    with factory() as stale_session:
        cached_order = OrderRepository(stale_session).get_by_id(order_id)
        assert cached_order.status == OrderStatus.OPEN
        with factory() as session:
            OrderService(SqlAlchemyUnitOfWork(session)).close_order(order_id)
        with factory() as session:
            replacement = OrderService(SqlAlchemyUnitOfWork(session)).create_order(
                OrderCreate(table_id=table_id, items=[])
            )
            replacement_id = replacement.id

        with pytest.raises(OrderNotOpen):
            mutate(stale_session, operation, order_id, product_id)

    with factory() as session:
        original = OrderRepository(session).get_by_id(order_id)
        assert original.status == OrderStatus.CLOSED
        assert original.items == []
        assert session.get(Order, replacement_id).status == OrderStatus.OPEN
        assert session.get(Table, table_id).status == TableStatus.OCCUPIED


@pytest.mark.parametrize("operation", mutations)
def test_failed_mutation_rolls_back_changes_and_releases_lock(
    integration_session_factory: sessionmaker[Session],
    order_context: tuple[UUID, UUID, UUID],
    operation: str,
) -> None:
    factory = integration_session_factory
    table_id, order_id, product_id = order_context

    def fail_commit(_: Session) -> None:
        raise RuntimeError("simulated commit failure")

    with factory() as failed_session:
        event.listen(failed_session, "before_commit", fail_commit, once=True)
        with pytest.raises(RuntimeError, match="simulated commit failure"):
            mutate(failed_session, operation, order_id, product_id)

        # Keep the failed session open: closing it would mask a missing rollback.
        with factory() as next_session:
            next_session.execute(text("SET LOCAL lock_timeout = '2s'"))
            order = OrderRepository(next_session).get_by_id(order_id, for_update=True)
            assert order.status == OrderStatus.OPEN
            assert order.items == []
            assert next_session.get(Table, table_id).status == TableStatus.OCCUPIED
            OrderService(SqlAlchemyUnitOfWork(next_session)).close_order(order_id)

    with factory() as session:
        assert session.get(Order, order_id).status == OrderStatus.CLOSED
        assert session.get(Table, table_id).status == TableStatus.AVAIALABLE


@pytest.mark.parametrize("lookup", ["get_by_id", "get_open_by_table_id"])
def test_locked_read_refreshes_preloaded_items(
    integration_session_factory: sessionmaker[Session],
    order_context: tuple[UUID, UUID, UUID],
    lookup: str,
) -> None:
    factory = integration_session_factory
    table_id, order_id, product_id = order_context
    key = order_id if lookup == "get_by_id" else table_id

    with factory() as stale_session:
        cached_order = getattr(OrderRepository(stale_session), lookup)(key)
        assert cached_order.items == []

        with factory() as session:
            mutate(session, "add_order_items", order_id, product_id)

        refreshed = getattr(OrderRepository(stale_session), lookup)(
            key, for_update=True
        )

        assert refreshed.status == OrderStatus.OPEN
        assert len(refreshed.items) == 1
        assert refreshed.items[0].product_id == product_id
        assert refreshed.items[0].quantity == 2
        assert refreshed.items[0].unit_price == Decimal("9.50")


@pytest.mark.parametrize("lookup", ["get_by_id", "get_open_by_table_id"])
@pytest.mark.parametrize("for_update", [False, True])
def test_repository_reads_respect_optional_lock(
    integration_session_factory: sessionmaker[Session],
    order_context: tuple[UUID, UUID, UUID],
    lookup: str,
    for_update: bool,
) -> None:
    factory = integration_session_factory
    table_id, order_id, _ = order_context
    key = order_id if lookup == "get_by_id" else table_id
    reader_pid: Future[int] = Future()

    def read() -> UUID:
        with factory() as session:
            session.execute(text("SET LOCAL lock_timeout = '5s'"))
            reader_pid.set_result(session.scalar(select(func.pg_backend_pid())))
            order = getattr(OrderRepository(session), lookup)(
                key, for_update=for_update
            )
            assert order.status == OrderStatus.OPEN
            return order.id

    with factory() as owner:
        OrderRepository(owner).get_by_id(order_id, for_update=True)
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(read)
            try:
                if for_update:
                    assert_waiting_for_lock(factory, reader_pid.result(timeout=5))
                else:
                    assert future.result(timeout=3) == order_id
            finally:
                owner.rollback()
            assert future.result(timeout=5) == order_id
