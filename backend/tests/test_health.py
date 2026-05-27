"""Liveness/readiness endpoint + cross-cutting middleware tests."""

import pytest
from fastapi.testclient import TestClient

from app.core.settings import AppMeta


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_ok_when_db_reachable(client: TestClient) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == "ok"


@pytest.mark.parametrize(
    "header",
    [
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Referrer-Policy",
        "Permissions-Policy",
        "Content-Security-Policy",
        "Strict-Transport-Security",
    ],
)
def test_security_headers_are_attached(client: TestClient, header: str) -> None:
    """Every response should carry the baseline security headers."""
    response = client.get("/health")
    assert response.headers.get(header), f"missing {header}"


def test_production_environment_nulls_docs_urls() -> None:
    """AppMeta's validator drops docs_url/redoc_url when environment=production."""
    meta = AppMeta(environment="production")
    assert meta.is_production is True
    assert meta.docs_url is None
    assert meta.redoc_url is None

    dev = AppMeta(environment="development")
    assert dev.is_production is False
    assert dev.docs_url == "/docs"
    assert dev.redoc_url == "/redoc"
