from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from maitre_api.domain.enums import OrderStatus


class OrderCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    table_id: UUID


class OrderFilter(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    table_id = UUID | None
    status = OrderStatus | None


class OrderUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status = OrderStatus | None

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    table_id: UUID
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
