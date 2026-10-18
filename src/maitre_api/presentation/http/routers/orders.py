from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from maitre_api.application.schemas.order import (
    OrderCreate,
    OrderFilter,
    OrderItemCreate,
    OrderListResponse,
    OrderResponse,
)
from maitre_api.domain.exceptions.order import OrderDoesNotExists, OrderNotOpen
from maitre_api.domain.exceptions.product import ProductNotActive, ProductNotFound
from maitre_api.domain.exceptions.table import TableNotAvaiable, TableNotFound
from maitre_api.presentation.http.dependencies import OrderServiceDep

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate, service: OrderServiceDep) -> OrderResponse:
    try:
        return service.create_order(order)
    except (ProductNotActive, TableNotAvaiable) as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except (ProductNotFound, TableNotFound) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/{order_id}/items",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_order_items(
    order_id: UUID, order_items: list[OrderItemCreate], service: OrderServiceDep
) -> OrderResponse:
    try:
        return service.add_order_items(order_id, order_items)
    except (ProductNotActive, OrderNotOpen) as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except (ProductNotFound, OrderDoesNotExists) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/{order_id}/close",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
)
def close_order(
    order_id: UUID, service: OrderServiceDep
) -> OrderResponse:
    try:
        return service.close_order(order_id)
    except OrderDoesNotExists as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except OrderNotOpen as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
)
def cancel_order(
    order_id: UUID, service: OrderServiceDep
) -> OrderResponse:
    try:
        return service.cancel_order(order_id)
    except OrderDoesNotExists as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except OrderNotOpen as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get("", response_model=list[OrderListResponse], status_code=status.HTTP_200_OK)
def list_orders(
    filter: Annotated[OrderFilter, Query()], service: OrderServiceDep
) -> list[OrderListResponse]:
    return service.list_orders(filter)


@router.get("/{order_id}", response_model=OrderResponse, status_code=status.HTTP_200_OK)
def get_order_by_id(order_id: UUID, service: OrderServiceDep) -> OrderResponse:
    order = service.get_order_by_id(order_id)

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return order
