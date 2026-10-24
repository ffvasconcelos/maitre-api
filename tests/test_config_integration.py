from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, text
from testcontainers.community.postgres import PostgresContainer

from alembic import command
from maitre_api.config import Settings


def test_migrations_connect_with_special_credentials_and_without_local_settings(
    monkeypatch, tmp_path
) -> None:
    password = "p@ss:/%?#[]"
    with PostgresContainer(
        "postgres:17", username="test", password=password, dbname="maitre_test"
    ) as postgres:
        settings = Settings(
            _env_file=None,
            postgres_db="maitre_test",
            postgres_user="test",
            postgres_password=password,
            postgres_host=postgres.get_container_host_ip(),
            postgres_port=int(postgres.get_exposed_port(5432)),
        )
        config = Config(str(Path(__file__).parent.parent / "alembic.ini"))
        config.attributes["database_url"] = settings.database_url

        def unexpected_settings():
            raise AssertionError("Explicit migration URLs must not load Settings")

        monkeypatch.setattr("maitre_api.config.Settings", unexpected_settings)
        monkeypatch.chdir(tmp_path)
        command.upgrade(config, "head")

        engine = create_engine(settings.database_url)
        try:
            with engine.connect() as connection:
                assert (
                    connection.scalar(text("SELECT current_database()"))
                    == "maitre_test"
                )
                assert connection.scalar(
                    text("SELECT version_num FROM alembic_version")
                )
                assert (
                    connection.scalar(
                        text("SELECT enum_range(NULL::table_status)::text")
                    )
                    == "{AVAILABLE,OCCUPIED}"
                )
        finally:
            engine.dispose()
