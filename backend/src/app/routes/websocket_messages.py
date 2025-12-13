"""
WebSocket routes for real-time messaging.

This module contains WebSocket endpoints for real-time message delivery.
"""

import asyncio
import json
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.websocket import authenticate_websocket_user
from app.schemas.message import MessageCreate, MessagePublic
from app.services.conversation import conversation_service
from app.services.message import message_service

logger = logging.getLogger(__name__)
websocket_router = APIRouter()

# Active WebSocket connections: {conversation_id: [WebSocket, WebSocket, ...]}
# NOTE: For production with multiple backend instances, replace with Redis pub/sub
# to broadcast messages across all servers. See planning docs for implementation details.
active_connections: dict[uuid.UUID, list[WebSocket]] = {}
connection_locks: dict[uuid.UUID, asyncio.Lock] = {}


def get_conversation_lock(conversation_id: uuid.UUID) -> asyncio.Lock:
    """Get or create a lock for a conversation."""
    if conversation_id not in connection_locks:
        connection_locks[conversation_id] = asyncio.Lock()
    return connection_locks[conversation_id]


async def broadcast_message_to_conversation(conversation_id: uuid.UUID, message_json: str) -> None:
    """
    Broadcast a message to all active WebSocket connections in a conversation.

    Automatically removes dead connections that fail to receive the message.

    Args:
        conversation_id: Conversation UUID
        message_json: JSON string of MessagePublic to broadcast
    """
    lock = get_conversation_lock(conversation_id)
    async with lock:
        if conversation_id not in active_connections:
            return

        dead_connections = []
        for connection in active_connections[conversation_id]:
            try:
                await connection.send_text(message_json)
            except (WebSocketDisconnect, RuntimeError):
                # RuntimeError catches closed connections
                dead_connections.append(connection)

        # Remove dead connections
        for dead_conn in dead_connections:
            active_connections[conversation_id].remove(dead_conn)


async def add_websocket_connection(conversation_id: uuid.UUID, websocket: WebSocket) -> None:
    """
    Add a WebSocket connection to the active connections for a conversation.

    Args:
        conversation_id: Conversation UUID
        websocket: WebSocket connection to add
    """
    lock = get_conversation_lock(conversation_id)
    async with lock:
        if conversation_id not in active_connections:
            active_connections[conversation_id] = []
        active_connections[conversation_id].append(websocket)


async def remove_websocket_connection(conversation_id: uuid.UUID, websocket: WebSocket) -> None:
    """
    Remove a WebSocket connection from active connections.

    Args:
        conversation_id: Conversation UUID
        websocket: WebSocket connection to remove
    """
    lock = get_conversation_lock(conversation_id)
    async with lock:
        if conversation_id not in active_connections:
            return

        if websocket in active_connections[conversation_id]:
            active_connections[conversation_id].remove(websocket)

        # Clean up empty conversation entries
        if not active_connections[conversation_id]:
            del active_connections[conversation_id]
            # Clean up lock too
            connection_locks.pop(conversation_id, None)


async def verify_conversation_access(
    db: Session, conversation_id: uuid.UUID, user_id: uuid.UUID
) -> bool:
    """
    Verify that a conversation exists and user is a participant.

    Args:
        db: Database session
        conversation_id: Conversation UUID
        user_id: User UUID

    Returns:
        bool: True if conversation exists and user is participant, False otherwise
    """
    try:
        conversation_service.get_by_id(db, conversation_id)
        conversation_service.verify_participant(db, conversation_id, user_id)
    except (ValueError, LookupError, HTTPException):
        return False
    else:
        return True


async def handle_websocket_message(
    db: Session, conversation_id: uuid.UUID, user_id: uuid.UUID, content: str
) -> None:
    """
    Handle incoming WebSocket message: save to DB and broadcast to participants.

    Args:
        db: Database session
        conversation_id: Conversation UUID
        user_id: Sender user UUID
        content: Message content

    Raises:
        ValueError: If content validation fails
    """
    # Validate message content with schema
    try:
        validated_message = MessageCreate(content=content)
        validated_content = validated_message.content
    except (ValueError, TypeError) as e:
        msg = f"Invalid message content: {e}"
        raise ValueError(msg) from e

    message = message_service.create(db, conversation_id, user_id, validated_content)
    message_public = MessagePublic.model_validate(message)
    message_json = message_public.model_dump_json()
    await broadcast_message_to_conversation(conversation_id, message_json)


async def authenticate_websocket(
    websocket: WebSocket, db: Session, conversation_id: uuid.UUID
) -> tuple[bool, uuid.UUID | None]:
    """
    Authenticate WebSocket connection and verify access.

    Args:
        websocket: WebSocket connection
        db: Database session
        conversation_id: Conversation UUID

    Returns:
        tuple: (success, user_id) - success is True if authenticated, user_id is the authenticated user
    """
    result: tuple[bool, uuid.UUID | None] = (False, None)
    error_reason = ""

    try:
        # Wait for authentication message with timeout
        auth_data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
        auth_message = json.loads(auth_data)

        # Validate and authenticate
        if auth_message.get("type") != "auth":
            error_reason = "First message must be authentication"
        elif not auth_message.get("token"):
            error_reason = "Token missing in auth message"
        else:
            user = authenticate_websocket_user(db, auth_message["token"])
            if user is None:
                error_reason = "Authentication failed"
            elif not await verify_conversation_access(db, conversation_id, user.id):
                error_reason = "Conversation not found or access denied"
            else:
                # Success
                await websocket.send_json({"type": "auth_success"})
                result = (True, user.id)

    except TimeoutError:
        error_reason = "Authentication timeout"
    except (json.JSONDecodeError, WebSocketDisconnect):
        error_reason = "Invalid authentication message"

    # Close with error if authentication failed
    if error_reason:
        await websocket.close(code=1008, reason=error_reason)

    return result


async def process_websocket_message(
    websocket: WebSocket, db: Session, conversation_id: uuid.UUID, user_id: uuid.UUID, data: str
) -> bool:
    """
    Process a single WebSocket message.

    Args:
        websocket: WebSocket connection
        db: Database session
        conversation_id: Conversation UUID
        user_id: User UUID
        data: Raw message data

    Returns:
        bool: True to continue loop, False to break
    """
    # Parse JSON with error handling
    try:
        message_data = json.loads(data)
    except json.JSONDecodeError as e:
        await websocket.send_json({"error": "Invalid JSON format", "detail": str(e)})
        return True

    content = message_data.get("content", "").strip()
    if not content:
        return True

    try:
        await handle_websocket_message(db, conversation_id, user_id, content)
    except ValueError as e:
        await websocket.send_json({"error": "Validation error", "detail": str(e)})

    return True


@websocket_router.websocket("/ws/conversations/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """
    WebSocket endpoint for real-time messaging in a conversation.

    Authenticates user via token in first message, verifies they are a participant,
    then maintains persistent connection for sending/receiving messages.

    First message format: {"type": "auth", "token": "JWT_TOKEN"}
    Message format (send): {"content": "message text"}
    Message format (receive): Full MessagePublic JSON object

    Args:
        websocket: WebSocket connection
        conversation_id: Conversation UUID
        db: Database session (injected via dependency)

    Raises:
        WebSocket close with code 1008 if authentication fails or user not participant
    """
    # Accept connection first
    await websocket.accept()

    # Authenticate and verify access
    success, user_id = await authenticate_websocket(websocket, db, conversation_id)
    if not success or user_id is None:
        return

    # Register connection
    await add_websocket_connection(conversation_id, websocket)

    try:
        while True:
            try:
                data = await websocket.receive_text()
                should_continue = await process_websocket_message(
                    websocket, db, conversation_id, user_id, data
                )
                if not should_continue:
                    break

            except WebSocketDisconnect:
                break
            except (RuntimeError, OSError):
                logger.exception("WebSocket connection error")
                break
            except Exception:
                logger.exception("Error processing WebSocket message")
                try:
                    await websocket.send_json(
                        {
                            "error": "Failed to process message",
                            "detail": "An internal error occurred",
                        }
                    )
                except (WebSocketDisconnect, RuntimeError, OSError):
                    break

    finally:
        await remove_websocket_connection(conversation_id, websocket)
