"""Unit tests for the LLM helpers (query expansion)."""

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from app.core.llm import expand_query
from app.core.settings import settings


@pytest.mark.unit
class TestExpandQuery:
    def test_returns_raw_when_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings.llm, "expand_queries", False)
        assert expand_query("something to listen to music") == "something to listen to music"

    def test_appends_keywords_when_enabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings.llm, "expand_queries", True)
        fake = GenericFakeChatModel(messages=iter([AIMessage(content="headphones earbuds audio")]))
        monkeypatch.setattr("app.core.llm.get_chat_model", lambda: fake)
        assert expand_query("music") == "music headphones earbuds audio"

    def test_falls_back_to_raw_on_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings.llm, "expand_queries", True)

        def boom() -> object:
            raise RuntimeError("llm down")

        monkeypatch.setattr("app.core.llm.get_chat_model", boom)
        assert expand_query("music") == "music"


def _capture_provider(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    """Replace the model builder with a spy and return the dict it records into."""
    captured: dict[str, object] = {}

    def fake_build(provider: str, *, temperature: float | None = None) -> object:
        captured["provider"] = provider
        captured["temperature"] = temperature
        return object()

    monkeypatch.setattr("app.core.llm._build_chat_model", fake_build)
    return captured


@pytest.mark.unit
class TestProviderRouting:
    def test_assist_model_prefers_assist_provider(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured = _capture_provider(monkeypatch)
        monkeypatch.setattr(settings.llm, "provider", "ollama")
        monkeypatch.setattr(settings.llm, "assist_provider", "anthropic")

        from app.core.llm import get_assist_model

        get_assist_model()
        assert captured["provider"] == "anthropic"

    def test_assist_model_falls_back_to_global(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured = _capture_provider(monkeypatch)
        monkeypatch.setattr(settings.llm, "provider", "ollama")
        monkeypatch.setattr(settings.llm, "assist_provider", "")

        from app.core.llm import get_assist_model

        get_assist_model()
        assert captured["provider"] == "ollama"

    def test_chat_model_uses_global_provider(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured = _capture_provider(monkeypatch)
        monkeypatch.setattr(settings.llm, "provider", "anthropic")
        monkeypatch.setattr(settings.llm, "assist_provider", "ollama")

        from app.core.llm import get_chat_model

        get_chat_model()
        assert captured["provider"] == "anthropic"
