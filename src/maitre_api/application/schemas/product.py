from decimal import Decimal
from pydantic import BaseModel

class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: Decimal
    active: bool | None = True