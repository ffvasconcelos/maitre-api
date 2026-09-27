from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from maitre_api.config import Settings

engine = create_engine(
    Settings().database_url,
    echo=True,
    echo_pool=True,
)

SessionLocal = sessionmaker[Session](
    engine,
    autocommit=False,
    autoflush=False,
)
