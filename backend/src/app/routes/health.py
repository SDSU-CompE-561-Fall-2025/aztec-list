"""
Liveness and readiness endpoints.

`/health` is a cheap liveness probe (process is up, event loop responding).
`/ready` checks the dependencies the API actually needs to serve traffic:
the database, and Qdrant when AI features are enabled. Returns 503 when any
critical dependency is unreachable so platforms route traffic away.
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.settings import settings
from app.services.vector_store import vector_store

logger = logging.getLogger(__name__)

health_router = APIRouter(tags=["health"])


@health_router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe: returns 200 as long as the event loop is responsive."""
    return {"status": "ok"}


@health_router.get("/ready")
async def ready(response: Response, db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    """Readiness probe: checks DB (and Qdrant when AI features are enabled)."""
    checks: dict[str, str] = {}
    ok = True

    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        ok = False
        checks["database"] = f"error: {type(exc).__name__}"
        logger.exception("Readiness check failed: database")

    if settings.ai.enabled:
        try:
            vector_store.client.get_collections()
            checks["vector_store"] = "ok"
        except Exception as exc:
            ok = False
            checks["vector_store"] = f"error: {type(exc).__name__}"
            logger.exception("Readiness check failed: vector store")

    if not ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if ok else "degraded", "checks": checks}
