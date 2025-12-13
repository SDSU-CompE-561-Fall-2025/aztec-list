"""
Rate limiter instance for the application.

This module provides a centralized rate limiter instance that can be imported
and used as a decorator in route handlers throughout the application.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.settings import settings

# Create a single limiter instance to be shared across the application
# The enabled flag can be toggled via RATE_LIMIT__ENABLED environment variable
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000/hour"],
    enabled=settings.rate_limit.enabled,
)
