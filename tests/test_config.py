from io import StringIO
from pathlib import Path
from runpy import run_path
from unittest.mock import MagicMock

import pytest
from alembic.config import Config
from sqlalchemy.engine import make_url

from alembic import command
from maitre_api.config import Settings

ROOT = Path(__file__).parent.parent


def make_settings(**overrides) -> Settings:
    return Settings(
        _env_file=None,
        postgres_db="maitre_test",
        postgres_user="user@name:/%",
        postgres_password="p@ss:/%?#[]",
        postgres_host="localhost",
        postgres_port=5432,
        **overrides,
    )


def test_database_url_preserves_special_characters() -> None:
    settings = make_settings()

    url = settings.database_url
    parsed = make_url(url.render_as_string(hide_password=False))

    assert parsed.username == settings.postgres_user
    assert parsed.password == settings.postgres_password
    assert parsed.host == settings.postgres_host
    assert parsed.port == settings.postgres_port
    assert parsed.database == settings.postgres_db
    assert parsed.drivername == "postgresql+psycopg"


def test_sql_logging_is_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("SQL_ECHO", raising=False)
    monkeypatch.delenv("SQL_ECHO_POOL", raising=False)

    settings = make_settings()

    assert settings.sql_echo is False
    assert settings.sql_echo_pool is False


def test_sql_logging_can_be_enabled_through_environment(monkeypatch) -> None:
    monkeypatch.setenv("SQL_ECHO", "true")
    monkeypatch.setenv("SQL_ECHO_POOL", "true")

    settings = make_settings()

    assert settings.sql_echo is True
    assert settings.sql_echo_pool is True


@pytest.mark.parametrize(
    "echo, echo_pool", [(False, False), (True, False), (False, True)]
)
def test_engine_uses_the_configured_logging_options(
    monkeypatch, echo, echo_pool
) -> None:
    settings = make_settings(sql_echo=echo, sql_echo_pool=echo_pool)
    create_engine = MagicMock()
    monkeypatch.setattr("maitre_api.config.Settings", lambda: settings)
    monkeypatch.setattr("sqlalchemy.create_engine", create_engine)

    run_path(str(ROOT / "src/maitre_api/infrastructure/database/session.py"))

    create_engine.assert_called_once_with(
        settings.database_url, echo=echo, echo_pool=echo_pool
    )


@pytest.mark.parametrize("source", ["url", "string", "settings"])
def test_offline_migrations_accept_special_credentials_without_ini_interpolation(
    monkeypatch, tmp_path, source
) -> None:
    settings = make_settings()
    sql = StringIO()
    config = Config(str(ROOT / "alembic.ini"), output_buffer=sql)
    if source == "url":
        config.attributes["database_url"] = settings.database_url
    elif source == "string":
        config.attributes["database_url"] = settings.database_url.render_as_string(
            hide_password=False
        )

    def load_settings():
        assert source == "settings", "Settings must not be loaded for an explicit URL"
        return settings

    monkeypatch.setattr("maitre_api.config.Settings", load_settings)
    monkeypatch.chdir(tmp_path)

    command.upgrade(config, "head", sql=True)

    assert "CREATE TABLE tables" in sql.getvalue()
    assert "AVAILABLE" in sql.getvalue()
