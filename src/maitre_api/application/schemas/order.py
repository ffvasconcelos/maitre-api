from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import AliasPath, BaseModel, ConfigDict, Field, computed_field

from maitre_api.domain.enums import OrderStatus


class OrderItemCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: UUID
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    table_id: UUID
    items: list[OrderItemCreate]


class OrderFilter(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    table_id: UUID | None = None
    status: OrderStatus | None = None


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    product_name: str = Field(validation_alias=AliasPath("product", "name"))
    quantity: int
    unit_price: Decimal

    @computed_field
    @property
    def subtotal(self) -> Decimal:
        return self.quantity * self.unit_price

    created_at: datetime
    updated_at: datetime


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    table_id: UUID
    table_number: int = Field(validation_alias=AliasPath("table", "number"))
    status: OrderStatus
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime


class OrderListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    table_id: UUID
    table_number: int = Field(validation_alias=AliasPath("table", "number"))
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
