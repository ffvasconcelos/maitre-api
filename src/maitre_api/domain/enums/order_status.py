from enum import StrEnum


class OrderStatus(StrEnum):
    OPEN = "Aberto"
    CLOSED = "Fechado"
    CANCELLED = "Cancelado"

