from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

from maitre_api.application.schemas.product import ProductCreate
from maitre_api.application.services.product_service import ProductService
from maitre_api.infrastructure.database.models.product import Product


def make_service() -> tuple[ProductService, MagicMock]:
    uow = MagicMock()
    uow.__enter__.return_value = uow
    return ProductService(uow), uow


def test_create_product_persists_and_commits() -> None:
    service, uow = make_service()
    product_data = ProductCreate(name="Soup", price=Decimal("8.50"))
    product = Product(name=product_data.name, price=product_data.price)
    uow.products.create.return_value = product

    result = service.create_product(product_data)

    assert result is product
    uow.products.create.assert_called_once_with(product_data)
    uow.commit.assert_called_once_with()


def test_get_product_returns_repository_result_without_committing() -> None:
    service, uow = make_service()
    product_id = uuid4()
    product = Product(name="Soup", price=Decimal("8.50"))
    uow.products.get_by_id.return_value = product

    result = service.get_product(product_id)

    assert result is product
    uow.products.get_by_id.assert_called_once_with(product_id)
    uow.commit.assert_not_called()


def test_list_products_returns_repository_results_without_committing() -> None:
    service, uow = make_service()
    products = [Product(name="Soup", price=Decimal("8.50"))]
    uow.products.list.return_value = products

    result = service.list_products()

    assert result is products
    uow.products.list.assert_called_once_with()
    uow.commit.assert_not_called()
