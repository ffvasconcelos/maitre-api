from uuid import UUID


class ProductNotFound(Exception):
    def __init__(self, id: UUID):
        self.id = id

        super().__init__(f"O produto não existe ({id})")


class ProductNotActive(Exception):
    def __init__(self, id: UUID):
        self.id = id

        super().__init__(f"O produto não está ativo ({id})")
