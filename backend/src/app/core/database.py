from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.settings import settings


def _engine_kwargs(database_url: str) -> dict[str, Any]:
    """
    Pick pool + connect args based on the dialect.

    SQLite uses ``check_same_thread=False`` and its default pool because
    pool_size/max_overflow/pool_recycle do not apply (single file, no network).
    Network-backed engines (Postgres, MySQL, etc.) get sane pool defaults plus
    ``pool_pre_ping`` so stale connections are discarded instead of returning
    a broken session to a request.
    """
    if database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {
        "pool_pre_ping": True,
        "pool_size": settings.db.pool_size,
        "max_overflow": settings.db.max_overflow,
        "pool_recycle": settings.db.pool_recycle_seconds,
    }


engine = create_engine(
    settings.db.database_url,
    echo=settings.db.echo,
    **_engine_kwargs(settings.db.database_url),
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models using SQLAlchemy 2.0 style."""


def get_db() -> Generator[Session]:
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
