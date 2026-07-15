"""
Tests des outils Google Workspace — mock googleapiclient pour éviter OAuth et appels réseau.
"""

from unittest.mock import MagicMock, patch

import pytest

from mcp_servers.google_workspace import server as gws


@pytest.fixture(autouse=True)
def mock_credentials():
    with patch(
        "mcp_servers.google_workspace.adapters.workspace_client.get_credentials",
        return_value=MagicMock(),
    ):
        yield


# ── Google Drive ──────────────────────────────────────────────────────────────


@patch("mcp_servers.google_workspace.adapters.workspace_client.build")
def test_list_drive_files_returns_results(mock_build: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.files().list().execute.return_value = {
        "files": [
            {
                "id": "abc123",
                "name": "Rapport Q1",
                "mimeType": "application/vnd.google-apps.document",
                "modifiedTime": "2026-05-10T10:00:00Z",
            }
        ]
    }
    result = gws.list_drive_files("rapport")
    assert "Rapport Q1" in result
    assert "abc123" in result


@patch("mcp_servers.google_workspace.adapters.workspace_client.build")
def test_list_drive_files_empty(mock_build: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.files().list().execute.return_value = {"files": []}
    result = gws.list_drive_files("inexistant")
    assert "Aucun" in result


@patch("mcp_servers.google_workspace.adapters.workspace_client.build")
def test_read_drive_file_google_doc(mock_build: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.files().get().execute.return_value = {
        "mimeType": "application/vnd.google-apps.document",
        "name": "Rapport",
    }
    mock_service.files().export().execute.return_value = b"Contenu du document"
    result = gws.read_drive_file("abc123")
    assert "Contenu" in result


@patch("mcp_servers.google_workspace.adapters.workspace_client.build")
def test_read_drive_file_plain_text(mock_build: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.files().get().execute.return_value = {
        "mimeType": "text/plain",
        "name": "notes.txt",
    }
    mock_service.files().get_media().execute.return_value = b"Notes brutes"
    result = gws.read_drive_file("xyz789")
    assert "Notes brutes" in result


@patch("mcp_servers.google_workspace.adapters.workspace_client.build")
def test_create_drive_doc_returns_link(mock_build: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.documents().create().execute.return_value = {"documentId": "doc999"}
    result = gws.create_drive_doc("Mon rapport", "Contenu du rapport")
    assert "doc999" in result
    assert "docs.google.com" in result


# ── Gmail ─────────────────────────────────────────────────────────────────────


@patch("mcp_servers.google_workspace.adapters.workspace_client.build")
def test_list_emails_returns_results(mock_build: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.users().messages().list().execute.return_value = {"messages": [{"id": "msg1"}]}
    mock_service.users().messages().get().execute.return_value = {
        "payload": {
            "headers": [
                {"name": "From", "value": "alice@example.com"},
                {"name": "Subject", "value": "Bonjour"},
                {"name": "Date", "value": "2026-05-18T09:00:00Z"},
            ]
        }
    }
    result = gws.list_emails("is:unread")
    assert "alice@example.com" in result
    assert "Bonjour" in result


@patch("mcp_servers.google_workspace.adapters.workspace_client.build")
def test_list_emails_empty(mock_build: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.users().messages().list().execute.return_value = {"messages": []}
    result = gws.list_emails()
    assert "Aucun" in result


@patch("mcp_servers.google_workspace.adapters.workspace_client.build")
def test_send_email_confirms_recipient(mock_build: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    result = gws.send_email("bob@example.com", "Test", "Corps du message")
    assert "bob@example.com" in result


# ── Google Calendar ───────────────────────────────────────────────────────────


@patch("mcp_servers.google_workspace.adapters.workspace_client.build")
def test_list_events_returns_results(mock_build: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.events().list().execute.return_value = {
        "items": [{"summary": "Réunion équipe", "start": {"dateTime": "2026-05-19T10:00:00+02:00"}}]
    }
    result = gws.list_events()
    assert "Réunion équipe" in result


@patch("mcp_servers.google_workspace.adapters.workspace_client.build")
def test_list_events_empty(mock_build: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.events().list().execute.return_value = {"items": []}
    result = gws.list_events()
    assert "Aucun" in result


@patch("mcp_servers.google_workspace.adapters.workspace_client.build")
def test_create_event_returns_link(mock_build: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.events().insert().execute.return_value = {
        "htmlLink": "https://calendar.google.com/event?id=abc"
    }
    result = gws.create_event(
        "Réunion",
        "2026-05-20T14:00:00",
        "2026-05-20T15:00:00",
        "Discussion projet",
        "alice@example.com,bob@example.com",
    )
    assert "calendar.google.com" in result


@patch("mcp_servers.google_workspace.adapters.workspace_client.build")
def test_create_event_without_attendees(mock_build: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.events().insert().execute.return_value = {
        "htmlLink": "https://calendar.google.com/event?id=xyz"
    }
    result = gws.create_event("Solo", "2026-05-20T09:00:00", "2026-05-20T10:00:00")
    assert "calendar.google.com" in result
