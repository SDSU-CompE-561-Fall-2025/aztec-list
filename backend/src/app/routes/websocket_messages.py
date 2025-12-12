"""
WebSocket routes for real-time messaging.

This module contains WebSocket endpoints for real-time message delivery.
"""

import json
import logging
import uuid

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from app.core.database import SessionLocal
from app.core.websocket import authenticate_websocket_user
from app.schemas.message import MessagePublic
from app.services.conversation import conversation_service
from app.services.message import message_service

logger = logging.getLogger(__name__)
websocket_router = APIRouter()

# Active WebSocket connections: {conversation_id: [WebSocket, WebSocket, ...]}
# NOTE: For production with multiple backend instances, replace with Redis pub/sub
# to broadcast messages across all servers. See planning docs for implementation details.
active_connections: dict[uuid.UUID, list[WebSocket]] = {}


async def broadcast_message_to_conversation(conversation_id: uuid.UUID, message_json: str) -> None:
    """
    Broadcast a message to all active WebSocket connections in a conversation.

    Automatically removes dead connections that fail to receive the message.

    Args:
        conversation_id: Conversation UUID
        message_json: JSON string of MessagePublic to broadcast
    """
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


def add_websocket_connection(conversation_id: uuid.UUID, websocket: WebSocket) -> None:
    """
    Add a WebSocket connection to the active connections for a conversation.

    Args:
        conversation_id: Conversation UUID
        websocket: WebSocket connection to add
    """
    if conversation_id not in active_connections:
        active_connections[conversation_id] = []
    active_connections[conversation_id].append(websocket)


def remove_websocket_connection(conversation_id: uuid.UUID, websocket: WebSocket) -> None:
    """
    Remove a WebSocket connection from active connections.

    Args:
        conversation_id: Conversation UUID
        websocket: WebSocket connection to remove
    """
    if conversation_id not in active_connections:
        return

    if websocket in active_connections[conversation_id]:
        active_connections[conversation_id].remove(websocket)

    # Clean up empty conversation entries
    if not active_connections[conversation_id]:
        del active_connections[conversation_id]


async def verify_conversation_access(conversation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """
    Verify that a conversation exists and user is a participant.

    Args:
        conversation_id: Conversation UUID
        user_id: User UUID

    Returns:
        bool: True if conversation exists and user is participant, False otherwise
    """
    db = SessionLocal()
    try:
        conversation_service.get_by_id(db, conversation_id)
        conversation_service.verify_participant(db, conversation_id, user_id)
    except (ValueError, LookupError, HTTPException):
        return False
    else:
        return True
    finally:
        db.close()


async def handle_websocket_message(
    conversation_id: uuid.UUID, user_id: uuid.UUID, content: str
) -> None:
    """
    Handle incoming WebSocket message: save to DB and broadcast to participants.

    Args:
        conversation_id: Conversation UUID
        user_id: Sender user UUID
        content: Message content
    """
    db = SessionLocal()
    try:
        message = message_service.create(db, conversation_id, user_id, content)
        message_public = MessagePublic.model_validate(message)
        message_json = message_public.model_dump_json()
        await broadcast_message_to_conversation(conversation_id, message_json)
    finally:
        db.close()


@websocket_router.websocket("/ws/conversations/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: uuid.UUID,
    token: str = Query(..., description="JWT access token for authentication"),
) -> None:
    """
    WebSocket endpoint for real-time messaging in a conversation.

    Authenticates user via token query parameter, verifies they are a participant,
    then maintains persistent connection for sending/receiving messages.

    Message format (send): {"content": "message text"}
    Message format (receive): Full MessagePublic JSON object

    Args:
        websocket: WebSocket connection
        conversation_id: Conversation UUID
        token: JWT access token (query parameter)

    Raises:
        WebSocket close with code 1008 if authentication fails or user not participant
    """
    # Authenticate user
    user = authenticate_websocket_user(token)
    if user is None:
        await websocket.close(code=1008, reason="Authentication failed")
        return

    # Verify conversation access
    has_access = await verify_conversation_access(conversation_id, user.id)
    if not has_access:
        await websocket.close(code=1008, reason="Conversation not found or access denied")
        return

    # Accept connection and register
    await websocket.accept()
    add_websocket_connection(conversation_id, websocket)

    try:
        while True:
            try:
                # Receive and parse message
                data = await websocket.receive_text()

                # Parse JSON with error handling
                try:
                    message_data = json.loads(data)
                except json.JSONDecodeError as e:
                    # Send error back to client but don't disconnect
                    await websocket.send_json({"error": "Invalid JSON format", "detail": str(e)})
                    continue

                content = message_data.get("content", "").strip()

                if content:
                    await handle_websocket_message(conversation_id, user.id, content)

            except WebSocketDisconnect:
                # Client disconnected normally
                break
            except (RuntimeError, OSError):
                # Connection errors that should terminate the loop
                logger.exception("WebSocket connection error")
                break
            except Exception:
                # Log unexpected errors but don't crash
                logger.exception("Error processing WebSocket message")
                try:
                    await websocket.send_json(
                        {
                            "error": "Failed to process message",
                            "detail": "An internal error occurred",
                        }
                    )
                except (WebSocketDisconnect, RuntimeError, OSError):
                    # If we can't send error, connection is likely dead
                    break

    finally:
        # Always cleanup connection on exit
        remove_websocket_connection(conversation_id, websocket)
