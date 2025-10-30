"""
HTTP middleware for request logging and tracking.

This module provides:
- Request/response logging with correlation IDs
- Performance timing
- Configurable path exclusions
"""

import logging
import time
import uuid
from collections.abc import Callable
from http import HTTPStatus

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.settings import settings

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

    Reads configuration from app settings.
    """

    def __init__(self, app: ASGIApp) -> None:
        """
        Initialize middleware.

        Excluded paths are read from settings during middleware initialization.

        Args:
            app: ASGI application
        """
        super().__init__(app)
        self.excluded_paths = set(settings.logging.excluded_paths)

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
        if request.url.path in self.excluded_paths:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response

        start_time = time.perf_counter()
        client_host = request.client.host if request.client else "unknown"

        # Process request
        try:
            response = await call_next(request)
            process_time = time.perf_counter() - start_time

            # Determine log level based on status code
            log_level = (
                logging.WARNING if response.status_code >= HTTP_ERROR_THRESHOLD else logging.INFO
            )

            # Get status text from HTTPStatus enum
            try:
                status_text = HTTPStatus(response.status_code).phrase
            except ValueError:
                # Handle non-standard status codes
                status_text = "Unknown"

            logger.log(
                log_level,
                "%s %s %d %s",
                request.method,
                request.url.path,
                response.status_code,
                status_text,
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time_seconds": round(process_time, 3),
                    "client_host": client_host,
                    "user_agent": request.headers.get("user-agent", "unknown"),
                },
            )

            # Add custom headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}"

        except Exception as e:
            process_time = time.perf_counter() - start_time
            logger.exception(
                "%s %s failed",
                request.method,
                request.url.path,
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "process_time_seconds": round(process_time, 3),
                    "client_host": client_host,
                },
            )
            raise
        else:
            return response
