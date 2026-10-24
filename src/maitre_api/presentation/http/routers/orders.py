from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from maitre_api.application.schemas.order import (
    OrderCreate,
    OrderFilter,
    OrderItemCreate,
    OrderListResponse,
    OrderResponse,
)
from maitre_api.domain.entities.order import Order
from maitre_api.presentation.http.dependencies import OrderServiceDep
from maitre_api.presentation.http.schemas.error import error_responses

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(404, 409),
)
def create_order(order: OrderCreate, service: OrderServiceDep) -> Order:
    return service.create_order(order)


@router.post(
    "/{order_id}/items",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(404, 409),
)
def add_order_items(
    order_id: UUID, order_items: list[OrderItemCreate], service: OrderServiceDep
) -> Order:
    return service.add_order_items(order_id, order_items)


@router.post(
    "/{order_id}/close",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    responses=error_responses(404, 409),
)
def close_order(order_id: UUID, service: OrderServiceDep) -> Order:
    return service.close_order(order_id)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    responses=error_responses(404, 409),
)
def cancel_order(order_id: UUID, service: OrderServiceDep) -> Order:
    return service.cancel_order(order_id)


@router.get("", response_model=list[OrderListResponse], status_code=status.HTTP_200_OK)
def list_orders(
    filter: Annotated[OrderFilter, Query()], service: OrderServiceDep
) -> list[Order]:
    return service.list_orders(filter)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    responses=error_responses(404),
)
def get_order_by_id(order_id: UUID, service: OrderServiceDep) -> Order:
    return service.get_order_by_id(order_id)
