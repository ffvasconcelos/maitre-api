from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from maitre_api.application.schemas.table import TableCreate, TableResponse
from maitre_api.presentation.http.dependencies import TableServiceDep

router = APIRouter(prefix="/tables", tags=["Tables"])


@router.post("", response_model=TableResponse, status_code=status.HTTP_201_CREATED)
def create_table(
    table: TableCreate, service: TableServiceDep
) -> TableResponse:
    return service.create_table(table)


@router.get("", response_model=list[TableResponse], status_code=status.HTTP_200_OK)
def list_tables(service: TableServiceDep) -> list[TableResponse]:
    return service.list_tables()

@router.get(
    "/by_number/{number}", response_model=TableResponse, status_code=status.HTTP_200_OK
)
def get_table_by_number(number: int, service: TableServiceDep) -> TableResponse:
    table = service.get_table_by_number(number)

    if table is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found",
        )

    return table


@router.get(
    "/{table_id}", response_model=TableResponse, status_code=status.HTTP_200_OK
)
def get_table_by_id(table_id: UUID, service: TableServiceDep) -> TableResponse:
    table = service.get_table_by_id(table_id)

    if table is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found",
        )

    return table
