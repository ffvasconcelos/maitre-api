from collections.abc import Generator
from typing import Annotated

from fastapi.params import Depends
from sqlalchemy.orm import Session

from maitre_api.application.services import ProductService, TableService
from maitre_api.infrastructure.database.session import SessionLocal
from maitre_api.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DBSession = Annotated[Session, Depends(get_db)]


def get_product_service(db: DBSession) -> ProductService:
    uow = SqlAlchemyUnitOfWork(db)
    return ProductService(uow)


ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]


def get_table_service(db: DBSession) -> TableService:
    uow = SqlAlchemyUnitOfWork(db)
    return TableService(uow)


TableServiceDep = Annotated[TableService, Depends(get_table_service)]
