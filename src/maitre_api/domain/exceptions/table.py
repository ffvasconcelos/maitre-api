class TableNumberAlreadyExists(Exception):
    def __init__(self, number: int) -> None:
        self.number = number
        super().__init__(
            f"Já existe uma mesa com o número {number}."
        )


class TableNotAvaiable(Exception):
    def __init__(self, number: int) -> None:
        self.number = number
        super().__init__(
            f"A mesa {number} já está ocupada."
        )

class TableNotFound(Exception):
    def __init__(self, id: int) -> None:
        self.id = id
        super().__init__(
            f"Mesa não encontrada ({self.id})."
        )