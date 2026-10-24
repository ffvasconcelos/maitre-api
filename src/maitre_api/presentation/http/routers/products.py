from uuid import UUID

from fastapi import APIRouter, status

from maitre_api.application.schemas.product import ProductCreate, ProductResponse
from maitre_api.domain.entities.product import Product
from maitre_api.presentation.http.dependencies import ProductServiceDep
from maitre_api.presentation.http.schemas.error import error_responses

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, service: ProductServiceDep) -> Product:
    return service.create_product(product)


@router.get("", response_model=list[ProductResponse], status_code=status.HTTP_200_OK)
def list_products(service: ProductServiceDep) -> list[Product]:
    return service.list_products()


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    responses=error_responses(404),
)
def get_product_by_id(product_id: UUID, service: ProductServiceDep) -> Product:
    return service.get_product(product_id)
