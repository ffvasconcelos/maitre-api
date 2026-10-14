from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from maitre_api.application.schemas.product import ProductCreate, ProductResponse
from maitre_api.presentation.http.dependencies import ProductServiceDep

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product: ProductCreate, service: ProductServiceDep
) -> ProductResponse:
    return service.create_product(product)


@router.get("", response_model=list[ProductResponse], status_code=status.HTTP_200_OK)
def list_products(service: ProductServiceDep) -> list[ProductResponse]:
    return service.list_products()


@router.get(
    "/{product_id}", response_model=ProductResponse, status_code=status.HTTP_200_OK
)
def get_product_by_id(product_id: UUID, service: ProductServiceDep) -> ProductResponse:
    product = service.get_product(product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product
