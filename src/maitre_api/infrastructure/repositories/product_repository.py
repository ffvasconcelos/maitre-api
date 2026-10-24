import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from maitre_api.application.schemas.product import ProductCreate
from maitre_api.domain.entities.product import Product
from maitre_api.infrastructure.database.models.product import Product as ProductModel
from maitre_api.infrastructure.repositories.mappers import to_product


class ProductRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        model = self.session.get(ProductModel, product_id)
        return to_product(model) if model is not None else None

    def create(self, product_data: ProductCreate) -> Product:
        new_product = ProductModel(
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            active=product_data.active,
        )

        self.session.add(new_product)
        self.session.flush()
        return to_product(new_product)

    def list(self) -> list[Product]:
        return [
            to_product(model)
            for model in self.session.scalars(select(ProductModel)).all()
        ]
