"""
Integration tests for message and conversation REST API endpoints.

Tests cover conversation creation, listing, message retrieval, and pagination.
"""

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.user import User
from app.repository.conversation import ConversationRepository
from app.repository.message import MessageRepository


@pytest.fixture
def test_user2(db_session: Session) -> User:
    """Create a second test user for conversations."""
    from app.core.auth import get_password_hash
    from app.core.enums import UserRole

    user = User(
        id=uuid.uuid4(),
        username="testuser2",
        email="test2@example.edu",
        hashed_password=get_password_hash("testpassword123"),
        is_verified=True,
        role=UserRole.USER,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user3(db_session: Session) -> User:
    """Create a third test user for multi-conversation tests."""
    from app.core.auth import get_password_hash
    from app.core.enums import UserRole

    user = User(
        id=uuid.uuid4(),
        username="testuser3",
        email="test3@example.edu",
        hashed_password=get_password_hash("testpassword123"),
        is_verified=True,
        role=UserRole.USER,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_conversation(db_session: Session, test_user: User, test_user2: User) -> Conversation:
    """Create a test conversation between two users."""
    conversation = ConversationRepository.create(
        db_session,
        user_1_id=test_user.id,
        user_2_id=test_user2.id,
    )
    return conversation


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """Create authentication headers for test_user."""
    from app.core.auth import create_access_token

    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_user2(test_user2: User) -> dict[str, str]:
    """Create authentication headers for test_user2."""
    from app.core.auth import create_access_token

    token = create_access_token({"sub": str(test_user2.id)})
    return {"Authorization": f"Bearer {token}"}


class TestCreateConversation:
    """Test conversation creation endpoint."""

    def test_create_new_conversation_success(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        test_user2: User,
        auth_headers: dict[str, str],
    ):
        """Test creating a new conversation between two users."""
        response = client.post(
            "/api/v1/messages/conversations",
            json={"other_user_id": str(test_user2.id)},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["user_1_id"] in [str(test_user.id), str(test_user2.id)]
        assert data["user_2_id"] in [str(test_user.id), str(test_user2.id)]
        assert "created_at" in data

        # Verify conversation exists in database
        conversation = ConversationRepository.get_by_id(db_session, uuid.UUID(data["id"]))
        assert conversation is not None

    def test_create_conversation_returns_existing(
        self,
        client: TestClient,
        test_user: User,
        test_user2: User,
        test_conversation: Conversation,
        auth_headers: dict[str, str],
    ):
        """Test that creating duplicate conversation returns existing one."""
        response = client.post(
            "/api/v1/messages/conversations",
            json={"other_user_id": str(test_user2.id)},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == str(test_conversation.id)

    def test_create_conversation_with_self_fails(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test that user cannot create conversation with themselves."""
        response = client.post(
            "/api/v1/messages/conversations",
            json={"other_user_id": str(test_user.id)},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot create" in response.json()["detail"].lower()
        assert "with yourself" in response.json()["detail"].lower()

    def test_create_conversation_with_nonexistent_user_fails(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ):
        """Test creating conversation with non-existent user fails."""
        fake_user_id = uuid.uuid4()
        response = client.post(
            "/api/v1/messages/conversations",
            json={"other_user_id": str(fake_user_id)},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_conversation_without_auth_fails(
        self,
        client: TestClient,
        test_user2: User,
    ):
        """Test that conversation creation requires authentication."""
        response = client.post(
            "/api/v1/messages/conversations",
            json={"other_user_id": str(test_user2.id)},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_conversation_invalid_uuid_fails(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ):
        """Test creating conversation with invalid UUID fails."""
        response = client.post(
            "/api/v1/messages/conversations",
            json={"other_user_id": "not-a-uuid"},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetConversations:
    """Test listing user's conversations endpoint."""

    def test_get_conversations_success(
        self,
        client: TestClient,
        test_user: User,
        test_conversation: Conversation,
        auth_headers: dict[str, str],
    ):
        """Test getting user's conversations."""
        response = client.get(
            "/api/v1/messages/conversations",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == str(test_conversation.id)

    def test_get_conversations_multiple(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        test_user2: User,
        test_user3: User,
        auth_headers: dict[str, str],
    ):
        """Test getting multiple conversations."""
        # Create two conversations
        conv1 = ConversationRepository.create(db_session, test_user.id, test_user2.id)
        conv2 = ConversationRepository.create(db_session, test_user.id, test_user3.id)

        response = client.get(
            "/api/v1/messages/conversations",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        conversation_ids = [conv["id"] for conv in data]
        assert str(conv1.id) in conversation_ids
        assert str(conv2.id) in conversation_ids

    def test_get_conversations_empty(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ):
        """Test getting conversations when user has none."""
        response = client.get(
            "/api/v1/messages/conversations",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_conversations_without_auth_fails(
        self,
        client: TestClient,
    ):
        """Test that listing conversations requires authentication."""
        response = client.get("/api/v1/messages/conversations")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_conversations_ordered_by_date(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        test_user2: User,
        test_user3: User,
        auth_headers: dict[str, str],
    ):
        """Test that conversations are ordered by creation date (newest first)."""
        # Create conversations in order
        conv1 = ConversationRepository.create(db_session, test_user.id, test_user2.id)
        conv2 = ConversationRepository.create(db_session, test_user.id, test_user3.id)

        response = client.get(
            "/api/v1/messages/conversations",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should be ordered newest first (conv2 before conv1)
        assert data[0]["id"] == str(conv2.id)
        assert data[1]["id"] == str(conv1.id)


class TestGetConversationMessages:
    """Test retrieving messages from a conversation."""

    def test_get_messages_empty_conversation(
        self,
        client: TestClient,
        test_conversation: Conversation,
        auth_headers: dict[str, str],
    ):
        """Test getting messages from conversation with no messages."""
        response = client.get(
            f"/api/v1/messages/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_messages_with_messages(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        test_conversation: Conversation,
        auth_headers: dict[str, str],
    ):
        """Test getting messages from conversation."""
        # Create some messages
        msg1 = MessageRepository.create(
            db_session, test_conversation.id, test_user.id, "First message"
        )
        msg2 = MessageRepository.create(
            db_session, test_conversation.id, test_user.id, "Second message"
        )

        response = client.get(
            f"/api/v1/messages/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == str(msg1.id)
        assert data[0]["content"] == "First message"
        assert data[1]["id"] == str(msg2.id)
        assert data[1]["content"] == "Second message"

    def test_get_messages_pagination_limit(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        test_conversation: Conversation,
        auth_headers: dict[str, str],
    ):
        """Test pagination with limit parameter."""
        # Create 5 messages
        for i in range(5):
            MessageRepository.create(
                db_session, test_conversation.id, test_user.id, f"Message {i + 1}"
            )

        response = client.get(
            f"/api/v1/messages/conversations/{test_conversation.id}/messages?limit=3",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3

    def test_get_messages_pagination_skip(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        test_conversation: Conversation,
        auth_headers: dict[str, str],
    ):
        """Test pagination with skip parameter."""
        # Create 5 messages
        messages = []
        for i in range(5):
            msg = MessageRepository.create(
                db_session, test_conversation.id, test_user.id, f"Message {i + 1}"
            )
            messages.append(msg)

        response = client.get(
            f"/api/v1/messages/conversations/{test_conversation.id}/messages?offset=2",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3  # 5 total - 2 skipped = 3
        assert data[0]["id"] == str(messages[2].id)

    def test_get_messages_pagination_limit_and_skip(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        test_conversation: Conversation,
        auth_headers: dict[str, str],
    ):
        """Test pagination with both limit and skip parameters."""
        # Create 10 messages
        messages = []
        for i in range(10):
            msg = MessageRepository.create(
                db_session, test_conversation.id, test_user.id, f"Message {i + 1}"
            )
            messages.append(msg)

        response = client.get(
            f"/api/v1/messages/conversations/{test_conversation.id}/messages?limit=3&offset=2",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3
        assert data[0]["id"] == str(messages[2].id)
        assert data[1]["id"] == str(messages[3].id)
        assert data[2]["id"] == str(messages[4].id)

    def test_get_messages_non_participant_forbidden(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        test_user2: User,
        test_user3: User,
        auth_headers: dict[str, str],
    ):
        """Test that non-participant cannot access conversation messages."""
        # Create conversation between user2 and user3 (not test_user)
        conversation = ConversationRepository.create(db_session, test_user2.id, test_user3.id)

        response = client.get(
            f"/api/v1/messages/conversations/{conversation.id}/messages",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_messages_nonexistent_conversation_fails(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ):
        """Test getting messages from non-existent conversation fails."""
        fake_conversation_id = uuid.uuid4()
        response = client.get(
            f"/api/v1/messages/conversations/{fake_conversation_id}/messages",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_messages_without_auth_fails(
        self,
        client: TestClient,
        test_conversation: Conversation,
    ):
        """Test that getting messages requires authentication."""
        response = client.get(f"/api/v1/messages/conversations/{test_conversation.id}/messages")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_messages_invalid_limit(
        self,
        client: TestClient,
        test_conversation: Conversation,
        auth_headers: dict[str, str],
    ):
        """Test that invalid limit parameter is rejected."""
        response = client.get(
            f"/api/v1/messages/conversations/{test_conversation.id}/messages?limit=0",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_messages_limit_too_high(
        self,
        client: TestClient,
        test_conversation: Conversation,
        auth_headers: dict[str, str],
    ):
        """Test that limit above maximum is rejected."""
        response = client.get(
            f"/api/v1/messages/conversations/{test_conversation.id}/messages?limit=101",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_messages_negative_offset(
        self,
        client: TestClient,
        test_conversation: Conversation,
        auth_headers: dict[str, str],
    ):
        """Test that negative offset parameter is rejected."""
        response = client.get(
            f"/api/v1/messages/conversations/{test_conversation.id}/messages?offset=-1",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_messages_ordered_oldest_first(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        test_conversation: Conversation,
        auth_headers: dict[str, str],
    ):
        """Test that messages are returned oldest first."""
        # Create messages in order
        msg1 = MessageRepository.create(db_session, test_conversation.id, test_user.id, "First")
        msg2 = MessageRepository.create(db_session, test_conversation.id, test_user.id, "Second")
        msg3 = MessageRepository.create(db_session, test_conversation.id, test_user.id, "Third")

        response = client.get(
            f"/api/v1/messages/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data[0]["id"] == str(msg1.id)
        assert data[1]["id"] == str(msg2.id)
        assert data[2]["id"] == str(msg3.id)

    def test_get_messages_includes_all_fields(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        test_conversation: Conversation,
        auth_headers: dict[str, str],
    ):
        """Test that message response includes all required fields."""
        MessageRepository.create(db_session, test_conversation.id, test_user.id, "Test message")

        response = client.get(
            f"/api/v1/messages/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        message = data[0]
        assert "id" in message
        assert "conversation_id" in message
        assert "sender_id" in message
        assert "content" in message
        assert "created_at" in message
        assert message["content"] == "Test message"
        assert message["sender_id"] == str(test_user.id)
