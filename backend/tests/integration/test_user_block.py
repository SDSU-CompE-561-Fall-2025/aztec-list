"""Integration tests for the user block feature and its enforcement points."""

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketDisconnect

from app.core.auth import create_access_token, get_password_hash
from app.core.enums import UserRole
from app.models.conversation import Conversation
from app.models.user import User
from app.repository.conversation import ConversationRepository
from app.repository.user_block import UserBlockRepository
from app.services.user_block import user_block_service


@pytest.fixture
def test_user2(db_session: Session) -> User:
    """A second regular user."""
    user = User(
        id=uuid.uuid4(),
        username="blockuser2",
        email="block2@example.edu",
        hashed_password=get_password_hash("testpassword123"),
        is_verified=True,
        role=UserRole.USER,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def headers_user2(test_user2: User) -> dict[str, str]:
    """Auth headers for the second user."""
    return {"Authorization": f"Bearer {create_access_token({'sub': str(test_user2.id)})}"}


# --- REST block / unblock ----------------------------------------------------------------


def test_block_user_succeeds(
    authenticated_client: TestClient, test_user: User, test_user2: User, db_session: Session
) -> None:
    response = authenticated_client.post(f"/api/v1/users/{test_user2.id}/block")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["blocked_user_id"] == str(test_user2.id)
    assert UserBlockRepository.is_blocked(db_session, test_user.id, test_user2.id) is True


def test_block_is_idempotent(authenticated_client: TestClient, test_user2: User) -> None:
    first = authenticated_client.post(f"/api/v1/users/{test_user2.id}/block")
    second = authenticated_client.post(f"/api/v1/users/{test_user2.id}/block")
    assert first.status_code == status.HTTP_201_CREATED
    assert second.status_code == status.HTTP_201_CREATED


def test_cannot_block_self(authenticated_client: TestClient, test_user: User) -> None:
    response = authenticated_client.post(f"/api/v1/users/{test_user.id}/block")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_cannot_block_admin(authenticated_client: TestClient, test_admin: User) -> None:
    response = authenticated_client.post(f"/api/v1/users/{test_admin.id}/block")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_block_nonexistent_user(authenticated_client: TestClient) -> None:
    response = authenticated_client.post(f"/api/v1/users/{uuid.uuid4()}/block")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_unblock_removes_block(
    authenticated_client: TestClient, test_user: User, test_user2: User, db_session: Session
) -> None:
    authenticated_client.post(f"/api/v1/users/{test_user2.id}/block")
    response = authenticated_client.delete(f"/api/v1/users/{test_user2.id}/block")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert UserBlockRepository.is_blocked(db_session, test_user.id, test_user2.id) is False


def test_unblock_when_not_blocked_is_noop(
    authenticated_client: TestClient, test_user2: User
) -> None:
    response = authenticated_client.delete(f"/api/v1/users/{test_user2.id}/block")
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_list_my_blocks(
    authenticated_client: TestClient, test_user2: User
) -> None:
    authenticated_client.post(f"/api/v1/users/{test_user2.id}/block")
    response = authenticated_client.get("/api/v1/users/me/blocks")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["count"] == 1
    assert body["items"][0]["blocked_user_id"] == str(test_user2.id)
    assert body["items"][0]["blocked_username"] == test_user2.username


# --- is_blocked_either_way truth table ---------------------------------------------------


def test_is_blocked_either_way(db_session: Session, test_user: User, test_user2: User) -> None:
    assert user_block_service.is_blocked_either_way(db_session, test_user.id, test_user2.id) is False
    user_block_service.block(db_session, test_user.id, test_user2.id)
    # Either direction now reports the pair as blocked.
    assert user_block_service.is_blocked_either_way(db_session, test_user.id, test_user2.id) is True
    assert user_block_service.is_blocked_either_way(db_session, test_user2.id, test_user.id) is True
    # Directional check is asymmetric.
    assert user_block_service.is_blocked(db_session, test_user.id, test_user2.id) is True
    assert user_block_service.is_blocked(db_session, test_user2.id, test_user.id) is False


# --- conversation-create gate ------------------------------------------------------------


def test_blocked_user_cannot_open_conversation(
    client: TestClient,
    headers_user2: dict[str, str],
    test_user: User,
    test_user2: User,
    db_session: Session,
) -> None:
    # test_user blocks test_user2; test_user2 then tries to DM test_user.
    user_block_service.block(db_session, test_user.id, test_user2.id)
    response = client.post(
        "/api/v1/messages/conversations",
        json={"other_user_id": str(test_user.id)},
        headers=headers_user2,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_blocker_conversation_list_hides_blocked(
    authenticated_client: TestClient,
    test_user: User,
    test_user2: User,
    db_session: Session,
) -> None:
    ConversationRepository.create(db_session, test_user.id, test_user2.id)
    # Before blocking, the conversation is visible.
    before = authenticated_client.get("/api/v1/messages/conversations").json()
    assert len(before) == 1
    # After blocking, the blocker no longer sees it.
    user_block_service.block(db_session, test_user.id, test_user2.id)
    after = authenticated_client.get("/api/v1/messages/conversations").json()
    assert after == []


def test_blocked_party_still_sees_conversation(
    client: TestClient,
    headers_user2: dict[str, str],
    test_user: User,
    test_user2: User,
    db_session: Session,
) -> None:
    ConversationRepository.create(db_session, test_user.id, test_user2.id)
    user_block_service.block(db_session, test_user.id, test_user2.id)
    # test_user2 (the blocked party) still sees the thread.
    response = client.get("/api/v1/messages/conversations", headers=headers_user2)
    assert len(response.json()) == 1


# --- WebSocket handshake gate ------------------------------------------------------------


def test_blocked_user_websocket_handshake_rejected(
    client: TestClient,
    test_user: User,
    test_user2: User,
    db_session: Session,
) -> None:
    conversation: Conversation = ConversationRepository.create(
        db_session, test_user.id, test_user2.id
    )
    # test_user blocks test_user2; test_user2's socket handshake must fail.
    user_block_service.block(db_session, test_user.id, test_user2.id)
    token = create_access_token({"sub": str(test_user2.id)})

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/conversations/{conversation.id}") as websocket:
            websocket.send_json({"type": "auth", "token": token})
            websocket.receive_json()
