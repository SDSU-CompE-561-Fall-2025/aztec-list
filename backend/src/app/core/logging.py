"""
Logging configuration and formatters.

This module provides:
- Custom log formatters (JSON and colored)
- Logging configuration utilities
- ANSI color codes for terminal output
"""

import json
import logging
from typing import ClassVar

from app.core.settings import LoggingSettings

# Standard log record attributes to exclude when adding extra fields
STANDARD_LOG_ATTRS = {
    "name",
    "msg",
    "args",
    "created",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "thread",
    "threadName",
    "exc_info",
    "exc_text",
    "stack_info",
    "taskName",
}

# HTTP status code ranges for colored output
HTTP_SUCCESS_MIN = 200
HTTP_SUCCESS_MAX = 300
HTTP_REDIRECT_MIN = 300
HTTP_REDIRECT_MAX = 400
HTTP_CLIENT_ERROR_MIN = 400
HTTP_CLIENT_ERROR_MAX = 500


class Colors:
    """ANSI color codes for terminal output."""

    # Reset
    RESET = "\033[0m"

    # Regular colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bold colors
    BOLD_RED = "\033[1;31m"
    BOLD_GREEN = "\033[1;32m"
    BOLD_YELLOW = "\033[1;33m"
    BOLD_BLUE = "\033[1;34m"
    BOLD_MAGENTA = "\033[1;35m"
    BOLD_CYAN = "\033[1;36m"

    # Background colors
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"


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

        # Add extra fields from the log record using dictionary comprehension
        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in STANDARD_LOG_ATTRS
        }
        log_data.update(extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Formatter that adds colors to log output based on log level and HTTP status.

    Color scheme:
    - 2xx (Success): Green
    - 3xx (Redirect): Cyan
    - 4xx (Client Error): Yellow
    - 5xx (Server Error): Red
    - Log levels: DEBUG=Blue, INFO=White, WARNING=Yellow, ERROR=Red, CRITICAL=Bold Red
    """

    # Color mapping for log levels
    LEVEL_COLORS: ClassVar[dict[int, str]] = {
        logging.DEBUG: Colors.BLUE,
        logging.INFO: Colors.WHITE,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.BOLD_RED,
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors based on level and status code."""
        # Get base formatted message
        message = super().format(record)

        # Determine color based on status code if available
        status_code = getattr(record, "status_code", None)
        if status_code is not None:
            if HTTP_SUCCESS_MIN <= status_code < HTTP_SUCCESS_MAX:  # Success
                color = Colors.GREEN
            elif HTTP_REDIRECT_MIN <= status_code < HTTP_REDIRECT_MAX:  # Redirect
                color = Colors.CYAN
            elif HTTP_CLIENT_ERROR_MIN <= status_code < HTTP_CLIENT_ERROR_MAX:  # Client error
                color = Colors.YELLOW
            else:  # Server error (5xx)
                color = Colors.BOLD_RED
        else:
            # Use log level color
            color = self.LEVEL_COLORS.get(record.levelno, Colors.WHITE)

        return f"{color}{message}{Colors.RESET}"


def configure_logging(logging_settings: LoggingSettings) -> None:
    """
    Configure application-wide logging from settings.

    Sets up structured logging with consistent formatting across the application.

    Args:
        logging_settings: LoggingSettings instance with all configuration
    """
    # Create handler with appropriate formatter
    handler = logging.StreamHandler()

    if logging_settings.use_json:
        handler.setFormatter(JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S"))
    else:
        # Human-readable colored format for local development
        handler.setFormatter(
            ColoredFormatter(
                logging_settings.format,
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, logging_settings.level.upper()),
        handlers=[handler],
        force=True,  # Override any existing configuration
    )

    # Configure uvicorn loggers
    logging.getLogger("uvicorn.access").setLevel(
        getattr(logging, logging_settings.uvicorn_access_level.upper())
    )
    logging.getLogger("uvicorn.error").setLevel(
        getattr(logging, logging_settings.uvicorn_error_level.upper())
    )
