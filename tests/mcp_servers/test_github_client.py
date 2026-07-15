"""
Tests de l'adapter GithubClient — traduction méthode -> appel PyGithub.
"""

from unittest.mock import MagicMock, patch

import pytest

from mcp_servers.github.adapters.github_client import GithubClient


def test_init_raises_without_token() -> None:
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(RuntimeError, match="GITHUB_TOKEN"):
            GithubClient()


@patch("mcp_servers.github.adapters.github_client.Github")
def test_init_uses_explicit_token_over_env(mock_gh_cls: MagicMock) -> None:
    GithubClient(token="explicit-token")
    mock_gh_cls.assert_called_once_with("explicit-token")


@patch("mcp_servers.github.adapters.github_client.Github")
def test_list_pulls_delegates_to_get_repo(mock_gh_cls: MagicMock) -> None:
    mock_repo = MagicMock()
    mock_gh_cls.return_value.get_repo.return_value = mock_repo
    client = GithubClient(token="t")

    client.list_pulls("owner/repo", "open")

    mock_gh_cls.return_value.get_repo.assert_called_once_with("owner/repo")
    mock_repo.get_pulls.assert_called_once_with(state="open")


@patch("mcp_servers.github.adapters.github_client.Github")
def test_search_code_builds_query_with_repo_filter(mock_gh_cls: MagicMock) -> None:
    client = GithubClient(token="t")

    client.search_code("owner/repo", "def authenticate")

    mock_gh_cls.return_value.search_code.assert_called_once_with("def authenticate repo:owner/repo")


@patch("mcp_servers.github.adapters.github_client.Github")
def test_create_issue_forwards_kwargs(mock_gh_cls: MagicMock) -> None:
    mock_repo = MagicMock()
    mock_gh_cls.return_value.get_repo.return_value = mock_repo
    client = GithubClient(token="t")

    client.create_issue("owner/repo", title="Bug", body="desc", labels=["bug"])

    mock_repo.create_issue.assert_called_once_with(title="Bug", body="desc", labels=["bug"])


@patch("mcp_servers.github.adapters.github_client.Github")
def test_recent_commits_uses_branch_as_sha(mock_gh_cls: MagicMock) -> None:
    mock_repo = MagicMock()
    mock_gh_cls.return_value.get_repo.return_value = mock_repo
    client = GithubClient(token="t")

    client.recent_commits("owner/repo", "develop")

    mock_repo.get_commits.assert_called_once_with(sha="develop")
