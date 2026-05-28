"""Unit tests for the MCP server tools (thin wrappers over the listing service)."""

import pytest

from app.mcp_server import server


@pytest.mark.unit
class TestMcpServer:
    def test_list_categories(self) -> None:
        categories = server.list_categories()
        assert "electronics" in categories
        assert len(categories) > 5

    def test_search_listings(self, db_session, test_listing, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("app.core.database.SessionLocal", lambda: db_session)
        results = server.search_listings(query="laptop")
        assert test_listing.title in [r["title"] for r in results]

    def test_get_listing(self, db_session, test_listing, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("app.core.database.SessionLocal", lambda: db_session)
        result = server.get_listing(str(test_listing.id))
        assert result["id"] == str(test_listing.id)
        assert result["title"] == test_listing.title
