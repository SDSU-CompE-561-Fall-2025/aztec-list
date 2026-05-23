"""Integration tests for the AI assistant (SSE chat + conversation endpoints)."""

import json
import uuid

import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from sqlalchemy.orm import Session

from app.core.auth import get_password_hash
from app.core.enums import Condition, UserRole
from app.core.settings import settings
from app.models.listing import Listing
from app.models.user import User
from app.repository.ai_conversation import AIConversationRepository

CHAT_URL = "/api/v1/ai/chat"


def _parse_sse(text: str) -> list[dict]:
    return [json.loads(line[6:]) for line in text.splitlines() if line.startswith("data: ")]


def _index_desk(db: Session, seller_id: uuid.UUID, store) -> Listing:
    desk = Listing(
        id=uuid.uuid4(),
        seller_id=seller_id,
        title="Wooden study desk",
        description="a sturdy desk for a dorm",
        price=40.0,
        category="furniture",
        condition=Condition.GOOD,
        is_active=True,
    )
    db.add(desk)
    db.commit()
    store.ensure_collection()
    store.upsert_listing(desk)
    return desk


@pytest.mark.integration
def test_ai_chat_streams_grounded_answer(
    authenticated_client: TestClient,
    db_session: Session,
    test_user: User,
    monkeypatch: pytest.MonkeyPatch,
    memory_vector_store,
) -> None:
    monkeypatch.setattr(settings.ai, "enabled", True)
    monkeypatch.setattr(settings.vector, "score_floor", 0.0)
    monkeypatch.setattr("app.services.rag.vector_store", memory_vector_store)
    fake = GenericFakeChatModel(messages=iter([AIMessage(content="The Wooden study desk fits best.")]))
    monkeypatch.setattr("app.services.ai_assistant.get_chat_model", lambda: fake)

    desk = _index_desk(db_session, test_user.id, memory_vector_store)

    response = authenticated_client.post(CHAT_URL, json={"message": "I need a desk"})

    assert response.status_code == 200
    events = _parse_sse(response.text)
    types = [e["type"] for e in events]
    assert types[0] == "start"
    assert "sources" in types
    assert types[-1] == "done"

    answer = "".join(e["content"] for e in events if e["type"] == "token")
    assert "desk" in answer.lower()

    sources_event = next(e for e in events if e["type"] == "sources")
    assert any(s["title"] == desk.title for s in sources_event["sources"])

    # Conversation + both turns persisted.
    conversation_id = events[0]["conversation_id"]
    convo = authenticated_client.get(f"/api/v1/ai/conversations/{conversation_id}").json()
    assert [m["role"] for m in convo["messages"]] == ["user", "assistant"]
    assert convo["messages"][1]["sources"][0]["title"] == desk.title


@pytest.mark.integration
def test_ai_chat_disabled_returns_503(
    authenticated_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings.ai, "enabled", False)
    response = authenticated_client.post(CHAT_URL, json={"message": "hi"})
    assert response.status_code == 503


@pytest.mark.integration
def test_ai_chat_requires_auth(client: TestClient) -> None:
    response = client.post(CHAT_URL, json={"message": "hi"})
    assert response.status_code == 401


@pytest.mark.integration
def test_conversations_list_and_ownership(
    authenticated_client: TestClient, db_session: Session, test_user: User
) -> None:
    mine = AIConversationRepository.create(db_session, test_user.id)
    other = User(
        id=uuid.uuid4(),
        username="other2",
        email="other2@example.edu",
        hashed_password=get_password_hash("password123"),
        is_verified=True,
        role=UserRole.USER,
    )
    db_session.add(other)
    db_session.commit()
    theirs = AIConversationRepository.create(db_session, other.id)

    listed = authenticated_client.get("/api/v1/ai/conversations").json()
    listed_ids = {c["id"] for c in listed}
    assert str(mine.id) in listed_ids
    assert str(theirs.id) not in listed_ids

    assert authenticated_client.get(f"/api/v1/ai/conversations/{theirs.id}").status_code == 404
