"""
WebSocket routes for real-time messaging.

This module contains WebSocket endpoints for real-time message delivery.

Production-hardening notes:

- Each inbound message acquires a **short-lived** SQLAlchemy session via ``SessionLocal``
  and closes it before the next ``receive_text``. Holding one session for the connection's
  whole lifetime would pin a pool connection and let SQLAlchemy's identity map drift on
  long-lived sockets.
- A per-(conversation, user) sliding-window **rate limit** caps message volume so the WS
  path cannot be flooded with unlimited DB writes + broadcasts (slowapi only guards HTTP).
- A per-user **connection cap** prevents a single account from exhausting the pool.
- The receive loop uses an ``asyncio.wait_for`` so idle / half-open sockets are closed
  instead of blocking a coroutine forever.
- For multi-instance deployments the ``active_connections`` dict still needs to move to
  Redis pub/sub; this module is single-process only.
"""

import asyncio
import json
import logging
import time
import uuid
from collections import deque
from contextlib import contextmanager, suppress
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core import database
from app.core.logging_safe import sanitize_log
from app.core.settings import settings
from app.core.websocket import authenticate_websocket_user
from app.schemas.message import MessageCreate, MessagePublic
from app.services.conversation import conversation_service
from app.services.message import message_service

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)
websocket_router = APIRouter()

# Active WebSocket connections: {conversation_id: [WebSocket, WebSocket, ...]}
# NOTE: For production with multiple backend instances, replace with Redis pub/sub
# to broadcast messages across all servers. See planning docs for implementation details.
active_connections: dict[uuid.UUID, list[WebSocket]] = {}
connection_locks: dict[uuid.UUID, asyncio.Lock] = {}

# Per-user open-connection counter (for the per-user connection cap) and a global lock
# protecting the counter. A user that disconnects abnormally is reconciled in the
# endpoint's `finally` block, so this counter never stays inflated past the socket close.
user_connection_counts: dict[uuid.UUID, int] = {}
user_count_lock = asyncio.Lock()

# Per-(conversation, user) sliding-window rate-limit buckets. A deque of monotonic
# timestamps, pruned on access. The dict grows with active conversations and shrinks
# when a conversation's last socket disconnects.
RateBucketKey = tuple[uuid.UUID, uuid.UUID]
rate_buckets: dict[RateBucketKey, deque[float]] = {}


@contextmanager
def _db_session() -> "Iterator[Session]":
    """
    Yield a short-lived SQLAlchemy session, closing it on exit.

    Resolves ``database.SessionLocal`` lazily so the test suite can swap in a
    sqlite-backed factory by rebinding ``app.core.database.SessionLocal``.
    """
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_conversation_lock(conversation_id: uuid.UUID) -> asyncio.Lock:
    """Get or create a lock for a conversation."""
    return connection_locks.setdefault(conversation_id, asyncio.Lock())


def _allow_message(conversation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """
    Sliding-window rate limit: True when this (conversation, user) is under the cap.

    Prunes timestamps older than the configured window from the bucket before checking.
    Each granted call records ``time.monotonic()`` in the bucket.
    """
    cfg = settings.websocket
    now = time.monotonic()
    cutoff = now - cfg.rate_limit_window_seconds

    bucket = rate_buckets.setdefault((conversation_id, user_id), deque())
    while bucket and bucket[0] < cutoff:
        bucket.popleft()

    if len(bucket) >= cfg.rate_limit_messages:
        return False

    bucket.append(now)
    return True


def _drop_rate_buckets_for_conversation(conversation_id: uuid.UUID) -> None:
    """Remove rate buckets keyed to this conversation (called when it goes empty)."""
    for key in [k for k in rate_buckets if k[0] == conversation_id]:
        del rate_buckets[key]


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
            _drop_rate_buckets_for_conversation(conversation_id)


async def _try_acquire_user_slot(user_id: uuid.UUID) -> bool:
    """Reserve a connection slot for a user; return False when the per-user cap is hit."""
    cap = settings.websocket.max_connections_per_user
    async with user_count_lock:
        current = user_connection_counts.get(user_id, 0)
        if current >= cap:
            return False
        user_connection_counts[user_id] = current + 1
        return True


async def _release_user_slot(user_id: uuid.UUID) -> None:
    """Release a previously reserved per-user connection slot."""
    async with user_count_lock:
        current = user_connection_counts.get(user_id, 0)
        if current <= 1:
            user_connection_counts.pop(user_id, None)
        else:
            user_connection_counts[user_id] = current - 1


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
    websocket: WebSocket, conversation_id: uuid.UUID, user_id: uuid.UUID, data: str
) -> bool:
    """
    Process a single WebSocket message.

    Opens its own short-lived DB session so the connection does not pin one for its
    whole lifetime. Returns True to continue the receive loop, False to break out.
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

    # Per-(conversation, user) rate-limit check before doing any DB work.
    if not _allow_message(conversation_id, user_id):
        await websocket.send_json(
            {"error": "Rate limit exceeded", "detail": "Slow down and try again shortly."}
        )
        return True

    try:
        with _db_session() as db:
            await handle_websocket_message(db, conversation_id, user_id, content)
    except ValueError as e:
        await websocket.send_json({"error": "Validation error", "detail": str(e)})

    return True


@websocket_router.websocket("/ws/conversations/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: uuid.UUID) -> None:
    """
    WebSocket endpoint for real-time messaging in a conversation.

    Authenticates user via token in first message, verifies they are a participant,
    then maintains a connection that opens a fresh DB session per inbound message.

    First message format: {"type": "auth", "token": "JWT_TOKEN"}
    Message format (send): {"content": "message text"}
    Message format (receive): Full MessagePublic JSON object

    Raises:
        WebSocket close with code 1008 if authentication fails or user not participant
        WebSocket close with code 1013 if the per-user connection cap is hit
    """
    # Accept connection first
    await websocket.accept()

    # Authenticate using a short-lived session, then close it before entering the loop.
    with _db_session() as auth_db:
        success, user_id = await authenticate_websocket(websocket, auth_db, conversation_id)
    if not success or user_id is None:
        return

    # Per-user connection cap (try-again-later).
    if not await _try_acquire_user_slot(user_id):
        await websocket.close(code=1013, reason="Too many active connections for this user")
        return

    # Register connection
    await add_websocket_connection(conversation_id, websocket)

    try:
        await _receive_loop(websocket, conversation_id, user_id)
    finally:
        await remove_websocket_connection(conversation_id, websocket)
        await _release_user_slot(user_id)


async def _receive_loop(
    websocket: WebSocket, conversation_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    """Pull messages off the socket until the peer disconnects or goes idle."""
    idle_timeout = settings.websocket.idle_timeout_seconds
    while True:
        try:
            data = await asyncio.wait_for(websocket.receive_text(), timeout=idle_timeout)
            should_continue = await process_websocket_message(
                websocket, conversation_id, user_id, data
            )
            if not should_continue:
                return
        except TimeoutError:
            # Sanitize the path-param-derived id before logging to keep CodeQL's
            # log-injection check happy (FastAPI's UUID coercion already blocks it,
            # but the taint analysis can't see that).
            logger.info("Closing idle WebSocket for conversation %s", sanitize_log(conversation_id))
            with suppress(RuntimeError, OSError):
                await websocket.close(code=1001, reason="Idle timeout")
            return
        except WebSocketDisconnect:
            return
        except (RuntimeError, OSError):
            logger.exception("WebSocket connection error")
            return
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
                return
