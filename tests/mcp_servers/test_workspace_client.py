"""
Tests de l'adapter WorkspaceClient — traduction méthode -> appel googleapiclient.
"""

from unittest.mock import MagicMock, patch

import pytest

from mcp_servers.google_workspace.adapters.workspace_client import WorkspaceClient


@pytest.fixture(autouse=True)
def mock_credentials():
    with patch(
        "mcp_servers.google_workspace.adapters.workspace_client.get_credentials",
        return_value=MagicMock(),
    ):
        yield


def _client() -> WorkspaceClient:
    return WorkspaceClient(["scope"], "credentials.json", "token.json")


@patch("mcp_servers.google_workspace.adapters.workspace_client.build")
def test_list_drive_files_returns_raw_files(mock_build: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.files().list().execute.return_value = {"files": [{"id": "abc"}]}

    result = _client().list_drive_files("rapport", 20)

    assert result == [{"id": "abc"}]
    assert mock_build.call_args.args[:2] == ("drive", "v3")


@patch("mcp_servers.google_workspace.adapters.workspace_client.build")
def test_read_drive_file_exports_google_doc(mock_build: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.files().get().execute.return_value = {
        "mimeType": "application/vnd.google-apps.document"
    }
    mock_service.files().export().execute.return_value = b"contenu doc"

    result = _client().read_drive_file("file1")

    assert result == "contenu doc"
    mock_service.files().export.assert_any_call(fileId="file1", mimeType="text/plain")


@patch("mcp_servers.google_workspace.adapters.workspace_client.build")
def test_read_drive_file_uses_get_media_for_plain_text(mock_build: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.files().get().execute.return_value = {"mimeType": "text/plain"}
    mock_service.files().get_media().execute.return_value = b"notes brutes"

    result = _client().read_drive_file("file2")

    assert result == "notes brutes"


@patch("mcp_servers.google_workspace.adapters.workspace_client.build")
def test_create_drive_doc_returns_document_id(mock_build: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.documents().create().execute.return_value = {"documentId": "doc42"}

    result = _client().create_drive_doc("Titre", "Contenu")

    assert result == "doc42"


@patch("mcp_servers.google_workspace.adapters.workspace_client.build")
def test_list_emails_carries_over_list_id_not_detail_id(mock_build: MagicMock) -> None:
    """Verrouille le comportement historique : l'id affiché vient de messages().list(),
    pas du détail metadata (qui ne contient pas forcément 'id')."""
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.users().messages().list().execute.return_value = {"messages": [{"id": "msg-1"}]}
    mock_service.users().messages().get().execute.return_value = {"payload": {"headers": []}}

    result = _client().list_emails("is:unread", 10)

    assert result[0]["id"] == "msg-1"


@patch("mcp_servers.google_workspace.adapters.workspace_client.build")
def test_send_email_encodes_message(mock_build: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    _client().send_email("bob@example.com", "Sujet", "Corps")

    mock_service.users().messages().send.assert_called_once()
    kwargs = mock_service.users().messages().send.call_args.kwargs
    assert "raw" in kwargs["body"]


@patch("mcp_servers.google_workspace.adapters.workspace_client.build")
def test_create_event_adds_attendees_when_given(mock_build: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.events().insert().execute.return_value = {"htmlLink": "https://x"}

    _client().create_event(
        "Titre", "2026-05-20T10:00:00", "2026-05-20T11:00:00", "", "a@x.com,b@x.com"
    )

    body = mock_service.events().insert.call_args.kwargs["body"]
    assert body["attendees"] == [{"email": "a@x.com"}, {"email": "b@x.com"}]


@patch("mcp_servers.google_workspace.adapters.workspace_client.build")
def test_create_event_no_attendees_key_when_empty(mock_build: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.events().insert().execute.return_value = {"htmlLink": "https://x"}

    _client().create_event("Titre", "2026-05-20T10:00:00", "2026-05-20T11:00:00", "", "")

    body = mock_service.events().insert.call_args.kwargs["body"]
    assert "attendees" not in body
