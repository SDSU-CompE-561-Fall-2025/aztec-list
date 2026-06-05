"""Integration tests for message reports and the admin review queue."""

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import create_access_token, get_password_hash
from app.core.enums import AdminActionType, MessageReportStatus, UserRole
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.repository.admin import AdminActionRepository
from app.repository.conversation import ConversationRepository
from app.repository.message import MessageRepository
from app.repository.message_report import MessageReportRepository


@pytest.fixture
def test_user2(db_session: Session) -> User:
    """The user who authored the reported message."""
    user = User(
        id=uuid.uuid4(),
        username="reportee2",
        email="reportee2@example.edu",
        hashed_password=get_password_hash("testpassword123"),
        is_verified=True,
        role=UserRole.USER,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def conversation(db_session: Session, test_user: User, test_user2: User) -> Conversation:
    """A conversation between test_user (reporter) and test_user2 (author)."""
    return ConversationRepository.create(db_session, test_user.id, test_user2.id)


@pytest.fixture
def their_message(db_session: Session, conversation: Conversation, test_user2: User) -> Message:
    """A message authored by test_user2 that test_user can report."""
    return MessageRepository.create(
        db_session, conversation.id, test_user2.id, "this is the offending message"
    )


@pytest.fixture
def headers_user2(test_user2: User) -> dict[str, str]:
    """Auth headers for the message author."""
    return {"Authorization": f"Bearer {create_access_token({'sub': str(test_user2.id)})}"}


@pytest.fixture
def reporter_headers(test_user: User) -> dict[str, str]:
    """Auth headers for the reporter (test_user)."""
    return {"Authorization": f"Bearer {create_access_token({'sub': str(test_user.id)})}"}


@pytest.fixture
def admin_headers(test_admin: User) -> dict[str, str]:
    """Auth headers for the reviewing admin."""
    return {"Authorization": f"Bearer {create_access_token({'sub': str(test_admin.id)})}"}


# --- report creation ---------------------------------------------------------------------


def test_report_message_succeeds(
    authenticated_client: TestClient, their_message: Message, db_session: Session
) -> None:
    response = authenticated_client.post(
        f"/api/v1/messages/{their_message.id}/report",
        json={"category": "harassment", "reason_text": "rude"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["category"] == "harassment"
    assert body["status"] == "open"
    # An excerpt of the reported message is captured for the queue.
    reports = MessageReportRepository.get_by_status(db_session, MessageReportStatus.OPEN)
    assert len(reports) == 1
    assert reports[0][0].message_excerpt == "this is the offending message"


def test_cannot_report_own_message(
    client: TestClient, headers_user2: dict[str, str], their_message: Message
) -> None:
    # test_user2 authored the message; reporting it should 400.
    response = client.post(
        f"/api/v1/messages/{their_message.id}/report",
        json={"category": "spam"},
        headers=headers_user2,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_non_participant_cannot_report(
    client: TestClient, their_message: Message, db_session: Session
) -> None:
    outsider = User(
        id=uuid.uuid4(),
        username="outsider",
        email="outsider@example.edu",
        hashed_password=get_password_hash("testpassword123"),
        is_verified=True,
        role=UserRole.USER,
    )
    db_session.add(outsider)
    db_session.commit()
    headers = {"Authorization": f"Bearer {create_access_token({'sub': str(outsider.id)})}"}
    response = client.post(
        f"/api/v1/messages/{their_message.id}/report",
        json={"category": "spam"},
        headers=headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_report_nonexistent_message(authenticated_client: TestClient) -> None:
    response = authenticated_client.post(
        f"/api/v1/messages/{uuid.uuid4()}/report", json={"category": "spam"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_my_reports(authenticated_client: TestClient, their_message: Message) -> None:
    authenticated_client.post(
        f"/api/v1/messages/{their_message.id}/report", json={"category": "scam"}
    )
    response = authenticated_client.get("/api/v1/reports/me")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


# --- admin queue + resolution ------------------------------------------------------------


def _file_report(client: TestClient, message_id: uuid.UUID, headers: dict[str, str]) -> uuid.UUID:
    """Helper: file a report with the given auth headers and return its id."""
    resp = client.post(
        f"/api/v1/messages/{message_id}/report",
        json={"category": "harassment"},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    return uuid.UUID(resp.json()["id"])


def test_admin_queue_lists_open_reports(
    client: TestClient,
    reporter_headers: dict[str, str],
    admin_headers: dict[str, str],
    their_message: Message,
    test_user: User,
    test_user2: User,
) -> None:
    _file_report(client, their_message.id, reporter_headers)
    response = client.get("/api/v1/admin/message-reports", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["count"] == 1
    item = body["items"][0]
    assert item["reporter"]["username"] == test_user.username
    assert item["target_user"]["username"] == test_user2.username
    assert item["message"]["content"] == "this is the offending message"


def test_queue_requires_admin(authenticated_client: TestClient) -> None:
    response = authenticated_client.get("/api/v1/admin/message-reports")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_dismiss_report(
    client: TestClient,
    reporter_headers: dict[str, str],
    admin_headers: dict[str, str],
    their_message: Message,
    db_session: Session,
) -> None:
    report_id = _file_report(client, their_message.id, reporter_headers)
    response = client.post(
        f"/api/v1/admin/message-reports/{report_id}/dismiss", headers=admin_headers
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    report = MessageReportRepository.get_by_id(db_session, report_id)
    assert report.status == MessageReportStatus.DISMISSED


def test_uphold_report_issues_strike(
    client: TestClient,
    reporter_headers: dict[str, str],
    admin_headers: dict[str, str],
    their_message: Message,
    test_user2: User,
    db_session: Session,
) -> None:
    report_id = _file_report(client, their_message.id, reporter_headers)
    response = client.post(
        f"/api/v1/admin/message-reports/{report_id}/uphold", json={}, headers=admin_headers
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "upheld"
    assert body["strike_issued"] is True
    assert body["strike_count"] == 1
    # The message author actually received a STRIKE admin action.
    actions = AdminActionRepository.get_by_target_user_id(db_session, test_user2.id)
    assert any(a.action_type == AdminActionType.STRIKE for a in actions)


def test_uphold_already_reviewed_conflicts(
    client: TestClient,
    reporter_headers: dict[str, str],
    admin_headers: dict[str, str],
    their_message: Message,
) -> None:
    report_id = _file_report(client, their_message.id, reporter_headers)
    client.post(f"/api/v1/admin/message-reports/{report_id}/dismiss", headers=admin_headers)
    # Second resolution on the same report must 409.
    response = client.post(
        f"/api/v1/admin/message-reports/{report_id}/uphold", json={}, headers=admin_headers
    )
    assert response.status_code == status.HTTP_409_CONFLICT
