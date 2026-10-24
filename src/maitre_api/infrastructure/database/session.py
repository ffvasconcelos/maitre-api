from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from maitre_api.config import Settings

settings = Settings()

engine = create_engine(
    settings.database_url,
    echo=settings.sql_echo,
    echo_pool=settings.sql_echo_pool,
)

SessionLocal = sessionmaker[Session](
    engine,
    autocommit=False,
    autoflush=False,
)
