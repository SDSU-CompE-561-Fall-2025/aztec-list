from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.settings import settings

# Create database engine with configuration from settings
engine = create_engine(
    settings.db.database_url,
    echo=settings.db.echo,
    connect_args=(
        {"check_same_thread": False} if settings.db.database_url.startswith("sqlite") else {}
    ),
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session]:
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
