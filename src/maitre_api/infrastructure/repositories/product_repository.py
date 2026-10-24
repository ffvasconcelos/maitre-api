import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from maitre_api.application.schemas.product import ProductCreate
from maitre_api.infrastructure.database.models.product import Product


class ProductRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        return self.session.get(Product, product_id)

    def create(self, product_data: ProductCreate) -> Product:
        new_product = Product(
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            active=product_data.active,
        )

        self.session.add(new_product)
        self.session.flush()
        return new_product

    def list(self) -> list[Product]:
        return self.session.scalars(select(Product)).all()
