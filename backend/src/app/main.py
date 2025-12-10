from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.routes import api_router
from app.core.database import Base, engine
from app.core.logging import configure_logging
from app.core.middleware import RequestLoggingMiddleware, add_cache_headers_middleware
from app.core.rate_limiter import limiter
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
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
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

# Add rate limiter to app state and register exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

# Middleware is added in REVERSE order of execution
# Execution flow: Request → RequestLoggingMiddleware → CORSMiddleware → CacheHeaders → Routes → Response
# Add cache headers middleware first (executes last, adds cache headers to responses)
app.middleware("http")(add_cache_headers_middleware)

# Add CORS middleware second (executes second-to-last, before cache headers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allowed_origins,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allowed_methods,
    allow_headers=settings.cors.allowed_headers,
)

# Add request logging middleware third (executes first, outermost layer)
app.add_middleware(RequestLoggingMiddleware)

# Mount static files for serving uploaded images
# This serves files from the uploads directory at the /uploads URL path
# Images are cached for 1 year via cache headers middleware (immutable)
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

app.include_router(api_router)
