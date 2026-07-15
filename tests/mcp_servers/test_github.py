"""
Tests des outils GitHub — utilise un mock httpx pour éviter les appels réseau.
"""

from unittest.mock import MagicMock, patch

import pytest

from mcp_servers.github import server as gh


@pytest.fixture(autouse=True)
def reset_client():
    gh._client_instance = None
    yield
    gh._client_instance = None


def _mock_github(mock_cls: MagicMock, repo_data: dict | None = None) -> MagicMock:
    mock_repo = MagicMock()
    mock_instance = MagicMock()
    mock_instance.get_repo.return_value = mock_repo
    mock_cls.return_value = mock_instance
    return mock_repo


@patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"})
@patch("mcp_servers.github.adapters.github_client.Github")
def test_list_prs_returns_lines(mock_gh_cls: MagicMock) -> None:
    mock_repo = _mock_github(mock_gh_cls)
    pr = MagicMock()
    pr.number = 42
    pr.state = "open"
    pr.title = "Fix auth bug"
    pr.user.login = "alice"
    mock_repo.get_pulls.return_value = [pr]

    result = gh.list_prs("owner/repo")
    assert "#42" in result
    assert "Fix auth bug" in result


@patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"})
@patch("mcp_servers.github.adapters.github_client.Github")
def test_list_prs_empty(mock_gh_cls: MagicMock) -> None:
    mock_repo = _mock_github(mock_gh_cls)
    mock_repo.get_pulls.return_value = []
    result = gh.list_prs("owner/repo")
    assert "Aucune" in result


def test_list_prs_no_token() -> None:
    with patch.dict("os.environ", {}, clear=True):
        with patch("mcp_servers.github.server._client_instance", None):
            result = gh.list_prs("owner/repo")
    assert "GITHUB_TOKEN" in result


@patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"})
@patch("mcp_servers.github.adapters.github_client.Github")
def test_create_issue(mock_gh_cls: MagicMock) -> None:
    mock_repo = _mock_github(mock_gh_cls)
    issue = MagicMock()
    issue.number = 99
    issue.html_url = "https://github.com/owner/repo/issues/99"
    mock_repo.create_issue.return_value = issue

    result = gh.create_issue("owner/repo", "Bug critique", "Description du bug")
    assert "#99" in result
    assert "github.com" in result
