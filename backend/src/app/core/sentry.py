"""
Optional Sentry initialization.

A complete no-op when ``SENTRY__DSN`` is unset, so the dev path is unchanged and
tests stay offline. When a DSN is configured we wire the FastAPI + SQLAlchemy
integrations and tag events with the deployment environment.
"""

import logging

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.core.settings import settings

logger = logging.getLogger(__name__)


def init_sentry() -> None:
    """Initialize Sentry when a DSN is configured; otherwise do nothing."""
    if not settings.sentry.dsn:
        return

    environment = settings.sentry.environment or settings.app.environment
    sentry_sdk.init(
        dsn=settings.sentry.dsn,
        environment=environment,
        release=settings.app.version,
        traces_sample_rate=settings.sentry.traces_sample_rate,
        integrations=[
            FastApiIntegration(),
            StarletteIntegration(),
            SqlalchemyIntegration(),
        ],
        send_default_pii=False,
    )
    logger.info("Sentry initialized (environment=%s)", environment)
