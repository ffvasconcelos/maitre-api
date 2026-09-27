from collections.abc import Generator
from typing import Annotated

from fastapi.params import Depends
from sqlalchemy.orm import Session

from maitre_api.infrastructure.database.session import SessionLocal


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DB_SESSION = Annotated[Session, Depends(get_db)]
