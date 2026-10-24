from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from maitre_api.domain.exceptions.order import OrderNotFound, OrderNotOpen
from maitre_api.domain.exceptions.product import ProductNotActive, ProductNotFound
from maitre_api.domain.exceptions.table import (
    TableNotAvailable,
    TableNotFound,
    TableNumberAlreadyExists,
    TableNumberNotFound,
)
from maitre_api.presentation.http.schemas.error import ErrorResponse

DOMAIN_ERRORS: dict[type[Exception], tuple[int, str]] = {
    OrderNotFound: (status.HTTP_404_NOT_FOUND, "order_not_found"),
    OrderNotOpen: (status.HTTP_409_CONFLICT, "order_not_open"),
    ProductNotFound: (status.HTTP_404_NOT_FOUND, "product_not_found"),
    ProductNotActive: (status.HTTP_409_CONFLICT, "product_not_active"),
    TableNotFound: (status.HTTP_404_NOT_FOUND, "table_not_found"),
    TableNumberNotFound: (status.HTTP_404_NOT_FOUND, "table_number_not_found"),
    TableNotAvailable: (status.HTTP_409_CONFLICT, "table_not_available"),
    TableNumberAlreadyExists: (status.HTTP_409_CONFLICT, "table_number_already_exists"),
}


def _handler_for(
    status_code: int, code: str
) -> Callable[[Request, Exception], Awaitable[JSONResponse]]:
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        error = ErrorResponse(code=code, detail=str(exc))
        return JSONResponse(status_code=status_code, content=error.model_dump())

    return handler


def register_exception_handlers(app: FastAPI) -> None:
    for exception, (status_code, code) in DOMAIN_ERRORS.items():
        app.add_exception_handler(exception, _handler_for(status_code, code))
