from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from maitre_api.domain.enums import TableStatus


class TableCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    number: int = Field(gt=0)
    capacity: int = Field(gt=0)


class TableResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    number: int
    capacity: int
    status: TableStatus
    created_at: datetime
    updated_at: datetime
