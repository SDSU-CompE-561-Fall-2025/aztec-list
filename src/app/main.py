from fastapi import FastAPI

from app.api.v1.routes import api_router
from app.core.database import Base, engine
from app.core.settings import settings
import app.models  # noqa: F401

# Create database tables
# If the tables do not exist, create them
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app.title,
    description=settings.app.description,
    version=settings.app.version,
    docs_url=settings.app.docs_url,
    redoc_url=settings.app.redoc_url,
)

app.include_router(api_router)
