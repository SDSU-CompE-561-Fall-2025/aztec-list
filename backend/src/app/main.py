from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import api_router
from app.core.database import Base, engine
from app.core.middleware import RequestLoggingMiddleware, configure_logging
from app.core.settings import settings

# Configure logging
configure_logging(
    log_level=settings.logging.level,
    use_json=False  # Set to False for local development if you prefer readable logs
)

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

# Add CORS middleware (must be added before other middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allowed_origins,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allowed_methods,
    allow_headers=settings.cors.allowed_headers,
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

app.include_router(api_router)
