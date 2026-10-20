from unittest.mock import MagicMock

import pytest

from maitre_api.application.services import OrderService, ProductService, TableService
from maitre_api.presentation.http import dependencies


def test_get_db_closes_session_when_generator_finishes(monkeypatch) -> None:
    session = MagicMock()
    monkeypatch.setattr(dependencies, "SessionLocal", lambda: session)
    generator = dependencies.get_db()

    assert next(generator) is session
    generator.close()

    session.close.assert_called_once_with()


@pytest.mark.parametrize(
    ("factory", "service_type"),
    [
        (dependencies.get_product_service, ProductService),
        (dependencies.get_table_service, TableService),
        (dependencies.get_order_service, OrderService),
    ],
)
def test_service_factories_bind_the_request_session(factory, service_type) -> None:
    session = MagicMock()

    service = factory(session)

    assert isinstance(service, service_type)
    assert service._uow._session is session
