from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    detail: str


def error_responses(*status_codes: int) -> dict[int, dict[str, object]]:
    return {status_code: {"model": ErrorResponse} for status_code in status_codes}
