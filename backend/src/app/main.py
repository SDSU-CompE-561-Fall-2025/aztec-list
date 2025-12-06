from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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

# Create upload directory with absolute path before app initialization
upload_dir = Path(__file__).parent.parent.parent / "uploads"
upload_dir.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - runs on startup and shutdown."""
    # Startup: Verify upload directory exists
    if not upload_dir.exists():
        upload_dir.mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown: cleanup tasks can go here if needed


app = FastAPI(
    title=settings.app.title,
    description=settings.app.description,
    version=settings.app.version,
    docs_url=settings.app.docs_url,
    redoc_url=settings.app.redoc_url,
    lifespan=lifespan,
)

# Middleware is added in REVERSE order of execution
# Execution flow: Request → RequestLoggingMiddleware → CORSMiddleware → Routes → Response
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

# Mount static files for serving uploaded images
# This serves files from the uploads directory at the /uploads URL path
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

app.include_router(api_router)
