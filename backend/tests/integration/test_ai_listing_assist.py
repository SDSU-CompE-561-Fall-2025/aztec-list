"""Integration tests for AI seller-assist (B1 description generation)."""

import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from app.core.settings import settings

DESC_URL = "/api/v1/ai/generate-description"


@pytest.mark.integration
def test_generate_description_returns_text(
    authenticated_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings.ai, "enabled", True)
    fake = GenericFakeChatModel(
        messages=iter([AIMessage(content="A sturdy oak desk in good condition.")])
    )
    monkeypatch.setattr("app.services.ai_listing_assist.get_assist_model", lambda **_: fake)

    response = authenticated_client.post(
        DESC_URL, json={"title": "Oak desk", "category": "furniture", "condition": "good"}
    )

    assert response.status_code == 200
    assert "desk" in response.json()["description"].lower()


@pytest.mark.integration
def test_generate_description_disabled_returns_503(
    authenticated_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings.ai, "enabled", False)
    response = authenticated_client.post(DESC_URL, json={"title": "Oak desk"})
    assert response.status_code == 503


@pytest.mark.integration
def test_generate_description_requires_auth(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings.ai, "enabled", True)
    response = client.post(DESC_URL, json={"title": "Oak desk"})
    assert response.status_code == 401
