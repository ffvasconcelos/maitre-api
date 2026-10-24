from maitre_api.domain.entities import Order, OrderItem, Product, Table
from maitre_api.domain.entities.base import Entity
from maitre_api.infrastructure.database.base import BaseModel
from maitre_api.infrastructure.database.models.order import Order as OrderModel
from maitre_api.infrastructure.database.models.order_item import (
    OrderItem as OrderItemModel,
)
from maitre_api.infrastructure.database.models.product import Product as ProductModel
from maitre_api.infrastructure.database.models.table import Table as TableModel


def to_product(model: ProductModel) -> Product:
    return Product(
        id=model.id,
        name=model.name,
        description=model.description,
        price=model.price,
        active=model.active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_table(model: TableModel) -> Table:
    return Table(
        id=model.id,
        number=model.number,
        capacity=model.capacity,
        status=model.status,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_order_item(model: OrderItemModel) -> OrderItem:
    return OrderItem(
        id=model.id,
        product=to_product(model.product),
        quantity=model.quantity,
        unit_price=model.unit_price,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_order(model: OrderModel) -> Order:
    return Order(
        id=model.id,
        table=to_table(model.table),
        status=model.status,
        items=[to_order_item(item) for item in model.items],
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_order_item_model(item: OrderItem) -> OrderItemModel:
    return OrderItemModel(
        id=item.id,
        product_id=item.product_id,
        quantity=item.quantity,
        unit_price=item.unit_price,
    )


def update_timestamps(entity: Entity, model: BaseModel) -> None:
    entity.created_at = model.created_at
    entity.updated_at = model.updated_at
