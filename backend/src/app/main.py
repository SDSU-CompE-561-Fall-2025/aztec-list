import logging
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
from app.core.middleware import (
    RequestLoggingMiddleware,
    add_cache_headers_middleware,
    add_security_headers_middleware,
)
from app.core.rate_limiter import limiter
from app.core.sentry import init_sentry
from app.core.settings import settings
from app.routes.health import health_router
from app.routes.websocket_messages import websocket_router
from app.services.vector_store import vector_store

# Configure logging from settings
configure_logging(settings.logging)
logger = logging.getLogger(__name__)

# Initialize Sentry (no-op when SENTRY__DSN is unset). Must run before FastAPI() so
# the integrations can hook into request/response lifecycle.
init_sentry()

# Resolve the upload directory and ensure it exists before mounting StaticFiles below.
# StaticFiles raises at construction time if the directory is missing, and the mount
# call runs at import. Creating it lazily in `lifespan` is too late (e.g. fresh CI
# checkouts have no uploads/ and would crash before lifespan ever fires).
upload_dir = Path(__file__).parent.parent.parent / "uploads"
upload_dir.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan manager - runs on startup and shutdown."""
    # Startup: create tables (dev/test only). In production the schema is managed
    # by Alembic (`alembic upgrade head`); `create_all` is a convenience for SQLite
    # + tests, where there are no migrations to apply.
    if not settings.app.is_production:
        Base.metadata.create_all(bind=engine)

    # Ensure the vector search collection exists when AI features are enabled
    if settings.ai.enabled:
        try:
            vector_store.ensure_collection()
        except Exception:  # app must still start if Qdrant is unavailable
            logger.exception("Failed to initialize vector store collection")

    yield

    # Shutdown: release the vector store client (frees the embedded Qdrant lock)
    if settings.ai.enabled:
        vector_store.close()


app = FastAPI(
    title=settings.app.title,
    description=settings.app.description,
    version=settings.app.version,
    docs_url=settings.app.docs_url,
    redoc_url=settings.app.redoc_url,
    # Hide the OpenAPI schema in production - it's only useful for /docs and /redoc,
    # which are also off (set via AppMeta._hide_docs_in_prod).
    openapi_url=None if settings.app.is_production else "/openapi.json",
    lifespan=lifespan,
)

# Add rate limiter to app state and register exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

# Middleware is added in REVERSE order of execution
# Execution flow: Request → RequestLogging → CORS → SecurityHeaders → CacheHeaders → Routes
# Add cache headers middleware first (innermost; adds cache headers to image responses)
app.middleware("http")(add_cache_headers_middleware)

# Add security headers middleware (runs on every response)
app.middleware("http")(add_security_headers_middleware)

# Add CORS middleware second (executes second-to-last)
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

app.include_router(health_router)
app.include_router(api_router)
app.include_router(websocket_router)
