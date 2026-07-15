"""
Tests de l'authentification OAuth2 Google partagée (mcp_servers/common/google_auth.py).
"""

from unittest.mock import MagicMock, patch

from mcp_servers.common.google_auth import get_credentials


@patch("mcp_servers.common.google_auth.os.path.exists", return_value=False)
@patch("mcp_servers.common.google_auth.InstalledAppFlow")
def test_get_credentials_runs_oauth_flow_when_no_token_file(
    mock_flow_cls: MagicMock, mock_exists: MagicMock
) -> None:
    mock_exists.side_effect = lambda path: path == "credentials.json"
    mock_creds = MagicMock()
    mock_creds.to_json.return_value = "{}"
    mock_flow_cls.from_client_secrets_file.return_value.run_local_server.return_value = mock_creds

    with patch("builtins.open", MagicMock()):
        result = get_credentials(["scope"], "credentials.json", "token.json")

    assert result is mock_creds
    mock_flow_cls.from_client_secrets_file.assert_called_once_with("credentials.json", ["scope"])


@patch("mcp_servers.common.google_auth.os.path.exists", return_value=True)
def test_get_credentials_raises_when_credentials_file_missing(mock_exists: MagicMock) -> None:
    # token.json absent (le seul os.path.exists check qui matche est celui de credentials_file
    # renvoyant True dans ce test — donc on force explicitement le scénario "token absent,
    # credentials absent" via un side_effect dédié.
    mock_exists.side_effect = lambda path: False

    try:
        get_credentials(["scope"], "credentials.json", "token.json")
        raise AssertionError("devrait lever RuntimeError")
    except RuntimeError as e:
        assert "credentials.json" in str(e)


@patch("mcp_servers.common.google_auth.Credentials")
@patch("mcp_servers.common.google_auth.os.path.exists", return_value=True)
def test_get_credentials_returns_valid_cached_token(
    mock_exists: MagicMock, mock_creds_cls: MagicMock
) -> None:
    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_creds_cls.from_authorized_user_file.return_value = mock_creds

    result = get_credentials(["scope"], "credentials.json", "token.json")

    assert result is mock_creds
    mock_creds_cls.from_authorized_user_file.assert_called_once_with("token.json", ["scope"])


@patch("mcp_servers.common.google_auth.Request")
@patch("mcp_servers.common.google_auth.Credentials")
@patch("mcp_servers.common.google_auth.os.path.exists", return_value=True)
def test_get_credentials_refreshes_expired_token(
    mock_exists: MagicMock, mock_creds_cls: MagicMock, mock_request_cls: MagicMock
) -> None:
    mock_creds = MagicMock()
    mock_creds.valid = False
    mock_creds.expired = True
    mock_creds.refresh_token = "refresh-token"
    mock_creds.to_json.return_value = "{}"
    mock_creds_cls.from_authorized_user_file.return_value = mock_creds

    with patch("builtins.open", MagicMock()):
        result = get_credentials(["scope"], "credentials.json", "token.json")

    mock_creds.refresh.assert_called_once()
    assert result is mock_creds
