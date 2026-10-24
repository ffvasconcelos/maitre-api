from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(max_length=150)
    description: str | None = Field(default=None, max_length=250)
    price: Decimal = Field(max_digits=10, decimal_places=2)
    active: bool = True


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    price: Decimal
    active: bool
    created_at: datetime
    updated_at: datetime
