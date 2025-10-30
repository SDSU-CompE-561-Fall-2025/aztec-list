"""
Middleware components for request processing.

This module provides middleware for:
- Request/response logging with performance metrics
- Error tracking and correlation IDs
- Request context enrichment
"""

import json
import logging
import time
import uuid
from collections.abc import Callable
from http import HTTPStatus
from typing import ClassVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# HTTP status code threshold for error logging
HTTP_ERROR_THRESHOLD = 400


class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs logs as JSON for structured logging.

    Compatible with log aggregation tools like ELK, Datadog, CloudWatch, etc.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string."""
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields from the log record
        for key, value in record.__dict__.items():
            if key not in [
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'message', 'pathname', 'process', 'processName',
                'relativeCreated', 'thread', 'threadName', 'exc_info',
                'exc_text', 'stack_info', 'taskName'
            ]:
                log_data[key] = value

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)


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

    EXCLUDED_PATHS: ClassVar[set[str]] = {"/health", "/docs", "/redoc", "/openapi.json"}

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
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response

        start_time = time.perf_counter()
        client_host = request.client.host if request.client else "unknown"

        # Process request
        try:
            response = await call_next(request)
            process_time = time.perf_counter() - start_time

            # Determine log level and message based on status code
            log_level = (
                logging.WARNING if response.status_code >= HTTP_ERROR_THRESHOLD else logging.INFO
            )

            # Get status text from HTTPStatus enum
            try:
                status_text = HTTPStatus(response.status_code).phrase
                message = f"{request.method} {request.url.path} {response.status_code} {status_text}"
            except ValueError:
                # Handle non-standard status codes
                message = f"{request.method} {request.url.path} {response.status_code}"

            logger.log(
                log_level,
                message,
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

            return response

        except Exception as e:
            process_time = time.perf_counter() - start_time
            logger.exception(
                f"{request.method} {request.url.path} failed",
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


def configure_logging(log_level: str = "INFO", use_json: bool = True) -> None:
    """
    Configure application-wide logging.

    Sets up structured logging with consistent formatting across the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Whether to use JSON formatting (recommended for production)
    """
    # Create handler with appropriate formatter
    handler = logging.StreamHandler()

    if use_json:
        handler.setFormatter(JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S"))
    else:
        # Human-readable format for local development
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=[handler],
        force=True,  # Override any existing configuration
    )

    # Reduce noise from uvicorn
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
