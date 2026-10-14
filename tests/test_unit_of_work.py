from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from maitre_api.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def make_unit_of_work() -> tuple[SqlAlchemyUnitOfWork, MagicMock]:
    session = MagicMock(spec=Session)
    return SqlAlchemyUnitOfWork(session), session


def test_exit_rolls_back_when_not_committed() -> None:
    uow, session = make_unit_of_work()

    with uow:
        pass

    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()


def test_commit_prevents_rollback_on_exit() -> None:
    uow, session = make_unit_of_work()

    with uow:
        uow.commit()

    session.commit.assert_called_once_with()
    session.rollback.assert_not_called()


def test_exit_rolls_back_when_operation_raises() -> None:
    uow, session = make_unit_of_work()
    exception = RuntimeError("operation failed")

    try:
        with uow:
            raise exception
    except RuntimeError:
        pass

    session.rollback.assert_called_once_with()


def test_reentering_unit_of_work_resets_commit_state() -> None:
    uow, session = make_unit_of_work()

    with uow:
        uow.commit()

    with uow:
        pass

    session.commit.assert_called_once_with()
    session.rollback.assert_called_once_with()
