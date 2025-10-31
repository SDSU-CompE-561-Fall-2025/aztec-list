from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import api_router
from app.core.database import Base, engine
from app.core.logging import configure_logging
from app.core.middleware import RequestLoggingMiddleware
from app.core.settings import settings

# Configure logging from settings
configure_logging(settings.logging)

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

# Middleware is added in REVERSE order of execution
# Add CORS middleware first (executes last, closest to routes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allowed_origins,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allowed_methods,
    allow_headers=settings.cors.allowed_headers,
)

# Add request logging middleware second (executes first, outermost layer)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(api_router)
