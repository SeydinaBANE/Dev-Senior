"""
Tests de l'adapter SearchConsoleClient — traduction méthode -> appel googleapiclient.
"""

from unittest.mock import MagicMock, patch

from mcp_servers.seo.adapters.search_console_client import SearchConsoleClient


@patch("mcp_servers.seo.adapters.search_console_client.get_credentials")
@patch("mcp_servers.seo.adapters.search_console_client.build")
def test_top_queries_returns_rows(mock_build: MagicMock, mock_creds: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.searchanalytics().query().execute.return_value = {
        "rows": [{"keys": ["agent IA"], "clicks": 10}]
    }
    client = SearchConsoleClient(["scope"], "credentials.json", "token.json")

    rows = client.top_queries("https://example.com", "2026-05-01", "2026-05-18", 20, "fra")

    assert rows == [{"keys": ["agent IA"], "clicks": 10}]
    mock_build.assert_called_once_with("searchconsole", "v1", credentials=mock_creds.return_value)


@patch("mcp_servers.seo.adapters.search_console_client.get_credentials")
@patch("mcp_servers.seo.adapters.search_console_client.build")
def test_top_queries_fetches_fresh_credentials_each_call(
    mock_build: MagicMock, mock_creds: MagicMock
) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.searchanalytics().query().execute.return_value = {"rows": []}
    client = SearchConsoleClient(["scope"], "credentials.json", "token.json")

    client.top_queries("https://example.com", "2026-05-01", "2026-05-18", 20, "fra")
    client.top_queries("https://example.com", "2026-05-01", "2026-05-18", 20, "fra")

    assert mock_creds.call_count == 2  # pas de cache — appelé à chaque invocation


@patch("mcp_servers.seo.adapters.search_console_client.get_credentials")
@patch("mcp_servers.seo.adapters.search_console_client.build")
def test_page_performance_returns_rows(mock_build: MagicMock, mock_creds: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.searchanalytics().query().execute.return_value = {
        "rows": [{"keys": ["query"], "clicks": 5}]
    }
    client = SearchConsoleClient(["scope"], "credentials.json", "token.json")

    rows = client.page_performance(
        "https://example.com", "https://example.com/blog", "2026-05-01", "2026-05-18"
    )

    assert rows == [{"keys": ["query"], "clicks": 5}]
