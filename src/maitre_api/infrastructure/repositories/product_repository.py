from sqlalchemy.orm import Session

from sqlalchemy import select
import uuid

from maitre_api.application.schemas.product import ProductCreate
from maitre_api.infrastructure.database.models.product import Product


class ProductRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, id: uuid.UUID) -> Product | None:
        return self.session.get(Product, id)

    def create(self, data: ProductCreate) -> Product:
        new_product = Product(
            name=data.name,
            description=data.description,
            price=data.price,
            active=data.active,
        )

        self.session.add(new_product)
        self.session.flush()
        return new_product

    def list(self) -> list[Product]:
        return self.session.scalars(select(Product)).all()
