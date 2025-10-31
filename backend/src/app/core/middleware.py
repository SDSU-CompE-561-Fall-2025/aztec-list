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

# HTTP status code thresholds
HTTP_CLIENT_ERROR_THRESHOLD = 400
HTTP_SERVER_ERROR_THRESHOLD = 500

# Custom header names
CORRELATION_ID_HEADER = "X-Correlation-ID"
PROCESS_TIME_HEADER = "X-Process-Time"


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

    def _get_log_level(self, status_code: int) -> int:
        """
        Determine appropriate log level based on HTTP status code.

        Args:
            status_code: HTTP response status code

        Returns:
            Logging level (INFO, WARNING, or ERROR)
        """
        if status_code >= HTTP_SERVER_ERROR_THRESHOLD:
            return logging.ERROR  # 5xx - Server errors (our fault)
        if status_code >= HTTP_CLIENT_ERROR_THRESHOLD:
            return logging.WARNING  # 4xx - Client errors (user's fault)
        return logging.INFO  # 2xx/3xx - Success or redirects

    def _build_log_context(  # noqa: PLR0913
        self,
        correlation_id: str,
        request: Request,
        process_time: float,
        client_host: str,
        status_code: int | None = None,
        error: Exception | None = None,
    ) -> dict:
        """
        Build structured logging context with common fields.

        Args:
            correlation_id: Request correlation ID
            request: HTTP request object
            process_time: Request processing time in seconds
            client_host: Client IP address
            status_code: HTTP status code (optional)
            error: Exception if request failed (optional)

        Returns:
            Dictionary of log context fields
        """
        context = {
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "process_time_seconds": round(process_time, 3),
            "client_host": client_host,
        }

        if status_code is not None:
            context["status_code"] = status_code
            context["user_agent"] = request.headers.get("user-agent", "unknown")

        if error is not None:
            context["error"] = str(error)
            context["error_type"] = type(error).__name__

        return context

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
            response.headers[CORRELATION_ID_HEADER] = correlation_id
            return response

        start_time = time.perf_counter()
        client_host = request.client.host if request.client else "unknown"

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            process_time = time.perf_counter() - start_time
            logger.exception(
                "%s %s failed",
                request.method,
                request.url.path,
                extra=self._build_log_context(
                    correlation_id, request, process_time, client_host, error=e
                ),
            )
            raise

        # Log successful request
        process_time = time.perf_counter() - start_time
        log_level = self._get_log_level(response.status_code)

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
            extra=self._build_log_context(
                correlation_id,
                request,
                process_time,
                client_host,
                status_code=response.status_code,
            ),
        )

        # Add custom headers
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        response.headers[PROCESS_TIME_HEADER] = f"{process_time:.3f}"

        return response
