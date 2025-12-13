"""
Integration tests for WebSocket messaging.

Tests cover WebSocket connection, authentication, message sending/receiving,
error handling, and disconnection scenarios.
"""

import json
import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import create_access_token
from app.models.conversation import Conversation
from app.models.message import Message
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
def test_conversation(db_session: Session, test_user: User, test_user2: User) -> Conversation:
    """Create a test conversation between two users."""
    conversation = ConversationRepository.create(
        db_session,
        user_1_id=test_user.id,
        user_2_id=test_user2.id,
    )
    return conversation


class TestWebSocketConnection:
    """Test WebSocket connection establishment and basic operations."""

    def test_websocket_connect_success(
        self, client: TestClient, test_conversation: Conversation, test_user: User
    ):
        """Test successful WebSocket connection."""
        token = create_access_token({"sub": str(test_user.id)})

        with client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as websocket:
            # Send authentication
            websocket.send_json({"type": "auth", "token": token})

            # Receive auth success
            response = websocket.receive_json()
            assert response["type"] == "auth_success"

    def test_websocket_connect_invalid_conversation(self, client: TestClient, test_user: User):
        """Test WebSocket connection with nonexistent conversation."""
        token = create_access_token({"sub": str(test_user.id)})
        fake_conversation_id = uuid.uuid4()

        # Connection should be closed during authentication
        from starlette.websockets import WebSocketDisconnect

        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(f"/ws/conversations/{fake_conversation_id}") as websocket:
                # Send authentication
                websocket.send_json({"type": "auth", "token": token})
                websocket.receive_json()  # Should raise WebSocketDisconnect

    def test_websocket_connect_unauthorized_user(
        self, client: TestClient, test_conversation: Conversation, test_admin: User
    ):
        """Test WebSocket connection from user not in conversation."""
        # Admin is not a participant in test_conversation
        token = create_access_token({"sub": str(test_admin.id)})
        from starlette.websockets import WebSocketDisconnect

        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as websocket:
                # Send authentication
                websocket.send_json({"type": "auth", "token": token})
                websocket.receive_json()  # Should raise WebSocketDisconnect


class TestWebSocketAuthentication:
    """Test WebSocket authentication scenarios."""

    def test_authentication_missing_token(
        self, client: TestClient, test_conversation: Conversation
    ):
        """Test authentication with missing token."""
        from starlette.websockets import WebSocketDisconnect

        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as websocket:
                # Send auth without token
                websocket.send_json({"type": "auth"})
                websocket.receive_json()  # Should raise WebSocketDisconnect

    def test_authentication_invalid_token(
        self, client: TestClient, test_conversation: Conversation
    ):
        """Test authentication with invalid token."""
        from starlette.websockets import WebSocketDisconnect

        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as websocket:
                # Send invalid token
                websocket.send_json({"type": "auth", "token": "invalid_token_123"})
                websocket.receive_json()  # Should raise WebSocketDisconnect

    def test_authentication_wrong_message_type(
        self, client: TestClient, test_conversation: Conversation, test_user: User
    ):
        """Test first message is not auth type."""
        token = create_access_token({"sub": str(test_user.id)})
        from starlette.websockets import WebSocketDisconnect

        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as websocket:
                # Send wrong message type first
                websocket.send_json({"type": "message", "content": "hello"})
                websocket.receive_json()  # Should raise WebSocketDisconnect

    def test_authentication_timeout(self, client: TestClient, test_conversation: Conversation):
        """Test authentication timeout (no auth message sent)."""
        from starlette.websockets import WebSocketDisconnect

        # TestClient doesn't perfectly simulate async timeout, but test the concept
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as websocket:
                # Don't send anything - just try to receive (should close)
                websocket.receive_json()

    def test_authentication_invalid_json(self, client: TestClient, test_conversation: Conversation):
        """Test authentication with invalid JSON."""
        from starlette.websockets import WebSocketDisconnect

        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as websocket:
                # Send invalid JSON
                websocket.send_text("not json at all")
                websocket.receive_json()  # Should raise WebSocketDisconnect


class TestWebSocketMessaging:
    """Test sending and receiving messages via WebSocket."""

    def test_send_message_success(
        self,
        client: TestClient,
        db_session: Session,
        test_conversation: Conversation,
        test_user: User,
    ):
        """Test successfully sending a message."""
        token = create_access_token({"sub": str(test_user.id)})

        with client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as websocket:
            # Authenticate
            websocket.send_json({"type": "auth", "token": token})
            auth_response = websocket.receive_json()
            assert auth_response["type"] == "auth_success"

            # Send message
            message_content = "Hello, this is a test message!"
            websocket.send_json({"content": message_content})

            # Receive broadcasted message
            message_data = websocket.receive_json()
            assert "id" in message_data
            assert message_data["content"] == message_content
            assert message_data["sender_id"] == str(test_user.id)
            assert message_data["conversation_id"] == str(test_conversation.id)

            # Verify message was saved to database
            messages = MessageRepository.get_by_conversation(db_session, test_conversation.id)
            assert len(messages) == 1
            assert messages[0].content == message_content

    def test_send_multiple_messages(
        self,
        client: TestClient,
        db_session: Session,
        test_conversation: Conversation,
        test_user: User,
    ):
        """Test sending multiple messages in sequence."""
        token = create_access_token({"sub": str(test_user.id)})

        with client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as websocket:
            # Authenticate
            websocket.send_json({"type": "auth", "token": token})
            websocket.receive_json()  # auth success

            # Send multiple messages
            messages = ["First message", "Second message", "Third message"]
            for msg_content in messages:
                websocket.send_json({"content": msg_content})
                response = websocket.receive_json()
                assert response["content"] == msg_content

            # Verify all messages saved
            db_messages = MessageRepository.get_by_conversation(db_session, test_conversation.id)
            assert len(db_messages) == 3

    def test_send_message_with_emojis(
        self,
        client: TestClient,
        test_conversation: Conversation,
        test_user: User,
    ):
        """Test sending message with emojis and special characters."""
        token = create_access_token({"sub": str(test_user.id)})

        with client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as websocket:
            # Authenticate
            websocket.send_json({"type": "auth", "token": token})
            websocket.receive_json()

            # Send message with emojis
            message_content = "Hello! 👋 How are you? 😊🎉"
            websocket.send_json({"content": message_content})

            response = websocket.receive_json()
            assert response["content"] == message_content

    def test_send_empty_message_ignored(
        self,
        client: TestClient,
        db_session: Session,
        test_conversation: Conversation,
        test_user: User,
    ):
        """Test that empty messages are ignored."""
        token = create_access_token({"sub": str(test_user.id)})

        with client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as websocket:
            # Authenticate
            websocket.send_json({"type": "auth", "token": token})
            websocket.receive_json()

            # Send empty message
            websocket.send_json({"content": ""})

            # Send valid message after
            websocket.send_json({"content": "Valid message"})
            response = websocket.receive_json()
            assert response["content"] == "Valid message"

            # Only valid message should be saved
            messages = MessageRepository.get_by_conversation(db_session, test_conversation.id)
            assert len(messages) == 1

    def test_send_message_whitespace_only_ignored(
        self,
        client: TestClient,
        db_session: Session,
        test_conversation: Conversation,
        test_user: User,
    ):
        """Test that whitespace-only messages are ignored."""
        token = create_access_token({"sub": str(test_user.id)})

        with client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as websocket:
            # Authenticate
            websocket.send_json({"type": "auth", "token": token})
            websocket.receive_json()

            # Send whitespace-only message
            websocket.send_json({"content": "   \n\t   "})

            # No message should be saved
            messages = MessageRepository.get_by_conversation(db_session, test_conversation.id)
            assert len(messages) == 0


class TestWebSocketErrorHandling:
    """Test WebSocket error handling scenarios."""

    def test_send_message_with_html_tags_rejected(
        self,
        client: TestClient,
        test_conversation: Conversation,
        test_user: User,
    ):
        """Test that messages with HTML tags are rejected."""
        token = create_access_token({"sub": str(test_user.id)})

        with client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as websocket:
            # Authenticate
            websocket.send_json({"type": "auth", "token": token})
            websocket.receive_json()

            # Send message with HTML tags
            websocket.send_json({"content": "<script>alert('XSS')</script>"})

            # Should receive error response
            response = websocket.receive_json()
            assert "error" in response
            assert "Validation error" in response["error"]

    def test_send_message_too_long_rejected(
        self,
        client: TestClient,
        test_conversation: Conversation,
        test_user: User,
    ):
        """Test that messages over 5000 chars are rejected."""
        token = create_access_token({"sub": str(test_user.id)})

        with client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as websocket:
            # Authenticate
            websocket.send_json({"type": "auth", "token": token})
            websocket.receive_json()

            # Send message that's too long
            websocket.send_json({"content": "x" * 5001})

            # Should receive error response
            response = websocket.receive_json()
            assert "error" in response

    def test_send_invalid_json(
        self,
        client: TestClient,
        test_conversation: Conversation,
        test_user: User,
    ):
        """Test sending invalid JSON after authentication."""
        token = create_access_token({"sub": str(test_user.id)})

        with client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as websocket:
            # Authenticate
            websocket.send_json({"type": "auth", "token": token})
            websocket.receive_json()

            # Send invalid JSON
            websocket.send_text("this is not json")

            # Should receive error response
            response = websocket.receive_json()
            assert "error" in response
            assert "Invalid JSON" in response["error"]

    def test_send_message_missing_content_field(
        self,
        client: TestClient,
        db_session: Session,
        test_conversation: Conversation,
        test_user: User,
    ):
        """Test sending message without content field."""
        token = create_access_token({"sub": str(test_user.id)})

        with client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as websocket:
            # Authenticate
            websocket.send_json({"type": "auth", "token": token})
            websocket.receive_json()

            # Send message without content field
            websocket.send_json({"other_field": "value"})

            # Should be ignored (content is empty string)
            messages = MessageRepository.get_by_conversation(db_session, test_conversation.id)
            assert len(messages) == 0


class TestWebSocketBroadcasting:
    """Test message broadcasting to multiple connections."""

    def test_broadcast_to_multiple_connections(
        self,
        client: TestClient,
        test_conversation: Conversation,
        test_user: User,
        test_user2: User,
    ):
        """Test that messages are broadcasted to all connected users."""
        token1 = create_access_token({"sub": str(test_user.id)})
        token2 = create_access_token({"sub": str(test_user2.id)})

        # Connect both users
        with (
            client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as ws1,
            client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as ws2,
        ):
            # Authenticate both
            ws1.send_json({"type": "auth", "token": token1})
            ws1.receive_json()  # auth success

            ws2.send_json({"type": "auth", "token": token2})
            ws2.receive_json()  # auth success

            # User 1 sends message
            message_content = "Hello from user 1"
            ws1.send_json({"content": message_content})

            # Both should receive the message
            msg1 = ws1.receive_json()
            msg2 = ws2.receive_json()

            assert msg1["content"] == message_content
            assert msg2["content"] == message_content
            assert msg1["sender_id"] == str(test_user.id)
            assert msg2["sender_id"] == str(test_user.id)

    def test_broadcast_bidirectional(
        self,
        client: TestClient,
        test_conversation: Conversation,
        test_user: User,
        test_user2: User,
    ):
        """Test bidirectional message exchange."""
        token1 = create_access_token({"sub": str(test_user.id)})
        token2 = create_access_token({"sub": str(test_user2.id)})

        with (
            client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as ws1,
            client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as ws2,
        ):
            # Authenticate both
            ws1.send_json({"type": "auth", "token": token1})
            ws1.receive_json()
            ws2.send_json({"type": "auth", "token": token2})
            ws2.receive_json()

            # User 1 sends
            ws1.send_json({"content": "Hello from user 1"})
            msg1_to_1 = ws1.receive_json()
            msg1_to_2 = ws2.receive_json()
            assert msg1_to_1["content"] == "Hello from user 1"
            assert msg1_to_2["content"] == "Hello from user 1"

            # User 2 replies
            ws2.send_json({"content": "Hello from user 2"})
            msg2_to_2 = ws2.receive_json()
            msg2_to_1 = ws1.receive_json()
            assert msg2_to_2["content"] == "Hello from user 2"
            assert msg2_to_1["content"] == "Hello from user 2"


class TestWebSocketDisconnection:
    """Test WebSocket disconnection scenarios."""

    def test_graceful_disconnection(
        self,
        client: TestClient,
        db_session: Session,
        test_conversation: Conversation,
        test_user: User,
    ):
        """Test graceful WebSocket disconnection."""
        token = create_access_token({"sub": str(test_user.id)})

        with client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as websocket:
            # Authenticate and send message
            websocket.send_json({"type": "auth", "token": token})
            websocket.receive_json()

            websocket.send_json({"content": "Test message"})
            websocket.receive_json()

        # Connection closed, verify message was saved
        messages = MessageRepository.get_by_conversation(db_session, test_conversation.id)
        assert len(messages) == 1

    def test_one_user_disconnects_other_still_receives(
        self,
        client: TestClient,
        test_conversation: Conversation,
        test_user: User,
        test_user2: User,
    ):
        """Test that if one user disconnects, other still receives messages."""
        token1 = create_access_token({"sub": str(test_user.id)})
        token2 = create_access_token({"sub": str(test_user2.id)})

        # Connect user 1
        with client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as ws1:
            ws1.send_json({"type": "auth", "token": token1})
            ws1.receive_json()

            # Connect user 2
            with client.websocket_connect(f"/ws/conversations/{test_conversation.id}") as ws2:
                ws2.send_json({"type": "auth", "token": token2})
                ws2.receive_json()

                # Both connected, user 1 sends
                ws1.send_json({"content": "Message while both connected"})
                ws1.receive_json()
                ws2.receive_json()

            # User 2 disconnected, user 1 still connected
            ws1.send_json({"content": "Message after user 2 disconnected"})
            msg = ws1.receive_json()
            assert msg["content"] == "Message after user 2 disconnected"
