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
