from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.orm import Session, sessionmaker

from maitre_api.domain.enums import TableStatus
from maitre_api.infrastructure.database.models.table import Table


def test_initial_migrations_create_correct_table_status_labels(
    integration_session_factory: sessionmaker[Session],
) -> None:
    with integration_session_factory() as session:
        assert (
            session.scalar(text("SELECT enum_range(NULL::table_status)::text"))
            == "{AVAILABLE,OCCUPIED}"
        )
        available_id, occupied_id = uuid4(), uuid4()
        session.execute(
            text(
                "INSERT INTO tables (id, number, capacity, status) VALUES "
                "(:available_id, 400000000, 4, 'AVAILABLE'), "
                "(:occupied_id, 400000001, 4, 'OCCUPIED')"
            ),
            {"available_id": available_id, "occupied_id": occupied_id},
        )

        assert (
            session.scalar(select(Table.status).where(Table.id == available_id))
            == TableStatus.AVAILABLE
        )
        assert (
            session.scalar(select(Table.status).where(Table.id == occupied_id))
            == TableStatus.OCCUPIED
        )
        session.rollback()
