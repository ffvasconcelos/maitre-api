from collections.abc import Generator
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.community.postgres import PostgresContainer

from alembic import command


@pytest.fixture(scope="session")
def integration_session_factory() -> Generator[sessionmaker[Session]]:
    with PostgresContainer(
        "postgres:17", username="test", password="test", dbname="maitre_test"
    ) as postgres:
        database_url = (
            "postgresql+psycopg://test:test@"
            f"{postgres.get_container_host_ip()}:"
            f"{postgres.get_exposed_port(5432)}/maitre_test"
        )
        alembic_config = Config(Path(__file__).parent.parent / "alembic.ini")
        alembic_config.attributes["database_url"] = database_url
        command.upgrade(alembic_config, "head")

        engine = create_engine(database_url)
        try:
            yield sessionmaker(engine, expire_on_commit=False)
        finally:
            engine.dispose()
