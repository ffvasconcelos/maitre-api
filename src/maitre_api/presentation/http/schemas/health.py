from pydantic import BaseModel


class HealthErrorResponse(BaseModel):
    detail: str
