"""
Middleware components for request processing.

This module provides middleware for:
- Request/response logging with performance metrics
- Error tracking and correlation IDs
- Request context enrichment
"""

import logging
import time
import uuid
from collections.abc import Callable
from typing import ClassVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# HTTP status code threshold for error logging
HTTP_ERROR_THRESHOLD = 400


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.

    Logs:
    - Request method, path, and client information
    - Response status code and processing time
    - Correlation ID for request tracking
    - Error details for failed requests

    Excludes health check and docs endpoints from detailed logging.
    """

    EXCLUDED_PATHS: ClassVar[set[str]] = {"/docs", "/redoc", "/openapi.json", "/health"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log details.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler in chain

        Returns:
            Response: HTTP response from downstream handlers
        """
        # Generate correlation ID for request tracking
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Skip detailed logging for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Log request
        start_time = time.time()
        client_host = request.client.host if request.client else "unknown"

        logger.info(
            "Request started",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "client_host": client_host,
                "user_agent": request.headers.get("user-agent", "unknown"),
            },
        )

        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            log_level = (
                logging.WARNING if response.status_code >= HTTP_ERROR_THRESHOLD else logging.INFO
            )
            logger.log(
                log_level,
                "Request completed",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": f"{process_time:.3f}s",
                },
            )

            # Add custom headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}"

        except Exception as e:
            process_time = time.time() - start_time
            logger.exception(
                "Request failed",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "process_time": f"{process_time:.3f}s",
                },
            )
            raise
        else:
            return response


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure application-wide logging.

    Sets up structured logging with consistent formatting across the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Set uvicorn loggers to appropriate levels
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
