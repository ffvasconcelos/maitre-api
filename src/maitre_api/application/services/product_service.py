from uuid import UUID

from maitre_api.application.ports.unit_of_work import UnitOfWork
from maitre_api.application.schemas.product import ProductCreate
from maitre_api.domain.exceptions.product import ProductNotFound
from maitre_api.infrastructure.database.models.product import Product


class ProductService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def create_product(self, product_create: ProductCreate) -> Product:
        with self._uow as uow:
            product = uow.products.create(product_create)
            uow.commit()
            return product

    def get_product(self, product_id: UUID) -> Product | None:
        with self._uow as uow:
            product = uow.products.get_by_id(product_id)

            if product is None:
                raise ProductNotFound(product_id)

            return product

    def list_products(self) -> list[Product]:
        with self._uow as uow:
            return uow.products.list()
