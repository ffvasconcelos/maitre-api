class TableNumberAlreadyExists(Exception):
    def __init__(self, number: int) -> None:
        self.number = number
        super().__init__(
            f"Já existe uma mesa com o número {number}."
        )