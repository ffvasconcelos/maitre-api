from uuid import UUID


class TableNumberAlreadyExists(Exception):
    def __init__(self, number: int) -> None:
        self.number = number
        super().__init__(f"Já existe uma mesa com o número {number}.")


class TableNotAvailable(Exception):
    def __init__(self, number: int) -> None:
        self.number = number
        super().__init__(f"A mesa {number} já está ocupada.")


class TableNotFound(Exception):
    def __init__(self, id: UUID) -> None:
        self.id = id
        super().__init__(f"Mesa não encontrada ({self.id}).")


class TableNumberNotFound(Exception):
    def __init__(self, number: int) -> None:
        self.number = number
        super().__init__(f"Número da mesa não encontrado ({self.number}).")
