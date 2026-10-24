from uuid import UUID

from fastapi import APIRouter, status

from maitre_api.application.schemas.table import TableCreate, TableResponse
from maitre_api.domain.entities.table import Table
from maitre_api.presentation.http.dependencies import TableServiceDep
from maitre_api.presentation.http.schemas.error import error_responses

router = APIRouter(prefix="/tables", tags=["Tables"])


@router.post(
    "",
    response_model=TableResponse,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(409),
)
def create_table(table: TableCreate, service: TableServiceDep) -> Table:
    return service.create_table(table)


@router.get("", response_model=list[TableResponse], status_code=status.HTTP_200_OK)
def list_tables(service: TableServiceDep) -> list[Table]:
    return service.list_tables()


@router.get(
    "/by_number/{number}",
    response_model=TableResponse,
    status_code=status.HTTP_200_OK,
    responses=error_responses(404),
)
def get_table_by_number(number: int, service: TableServiceDep) -> Table:
    return service.get_table_by_number(number)


@router.get(
    "/{table_id}",
    response_model=TableResponse,
    status_code=status.HTTP_200_OK,
    responses=error_responses(404),
)
def get_table_by_id(table_id: UUID, service: TableServiceDep) -> Table:
    return service.get_table_by_id(table_id)
