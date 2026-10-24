from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from maitre_api.application.schemas.product import ProductCreate
from maitre_api.domain.entities.product import Product as ProductEntity
from maitre_api.infrastructure.database.models.product import Product
from maitre_api.infrastructure.repositories.product_repository import (
    ProductRepository,
)


def make_repository() -> tuple[ProductRepository, MagicMock]:
    session = MagicMock(spec=Session)
    return ProductRepository(session), session


def test_create_adds_and_flushes_product() -> None:
    repository, session = make_repository()
    product_data = ProductCreate(
        name="Soup",
        description="Daily special",
        price=Decimal("8.50"),
        active=False,
    )

    result = repository.create(product_data=product_data)

    assert isinstance(result, ProductEntity)
    assert result.name == product_data.name
    assert result.description == product_data.description
    assert result.price == product_data.price
    assert result.active is False
    model = session.add.call_args.args[0]
    assert isinstance(model, Product)
    assert model.name == result.name
    assert model.price == result.price
    session.flush.assert_called_once_with()


def test_get_by_id_uses_session_lookup() -> None:
    repository, session = make_repository()
    product_id = uuid4()
    product = Product(name="Soup", price=Decimal("8.50"))
    session.get.return_value = product

    result = repository.get_by_id(product_id=product_id)

    assert isinstance(result, ProductEntity)
    assert result.name == product.name
    assert result.price == product.price
    session.get.assert_called_once_with(Product, product_id)


def test_list_returns_all_products_from_query() -> None:
    repository, session = make_repository()
    products = [Product(name="Soup", price=Decimal("8.50"))]
    session.scalars.return_value.all.return_value = products

    result = repository.list()

    assert len(result) == 1
    assert isinstance(result[0], ProductEntity)
    assert result[0].name == products[0].name
    session.scalars.return_value.all.assert_called_once_with()
    statement = session.scalars.call_args.args[0]
    assert statement.column_descriptions[0]["entity"] is Product
    assert str(statement) == str(select(Product))


def test_missing_product_returns_none() -> None:
    repository, session = make_repository()
    session.get.return_value = None

    assert repository.get_by_id(uuid4()) is None
