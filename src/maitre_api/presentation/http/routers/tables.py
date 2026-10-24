from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from maitre_api.application.schemas.table import TableCreate, TableResponse
from maitre_api.domain.exceptions.table import (
    TableNotFound,
    TableNumberAlreadyExists,
    TableNumberNotFound,
)
from maitre_api.infrastructure.database.models.table import Table
from maitre_api.presentation.http.dependencies import TableServiceDep

router = APIRouter(prefix="/tables", tags=["Tables"])


@router.post("", response_model=TableResponse, status_code=status.HTTP_201_CREATED)
def create_table(table: TableCreate, service: TableServiceDep) -> Table:
    try:
        return service.create_table(table)
    except TableNumberAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get("", response_model=list[TableResponse], status_code=status.HTTP_200_OK)
def list_tables(service: TableServiceDep) -> list[Table]:
    return service.list_tables()


@router.get(
    "/by_number/{number}", response_model=TableResponse, status_code=status.HTTP_200_OK
)
def get_table_by_number(number: int, service: TableServiceDep) -> Table:
    try:
        table = service.get_table_by_number(number)
    except TableNumberNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    return table


@router.get("/{table_id}", response_model=TableResponse, status_code=status.HTTP_200_OK)
def get_table_by_id(table_id: UUID, service: TableServiceDep) -> Table:
    try:
        table = service.get_table_by_id(table_id)

    except TableNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    return table
