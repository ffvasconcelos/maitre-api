from uuid import UUID


class OrderNotOpen(Exception):
    def __init__(self, id: UUID) -> None:
            self.id = id
            super().__init__(
                f"O pedido já não está mais aberto ({id})."
            )


class OrderDoesNotExists(Exception):
    def __init__(self, id: UUID) -> None:
            self.id = id
            super().__init__(
                f"O pedido já não está mais aberto ({id})."
            )