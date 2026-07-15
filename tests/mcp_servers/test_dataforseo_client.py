"""
Tests de l'adapter DataForSeoClient — traduction méthode -> appel httpx.
"""

from unittest.mock import MagicMock, patch

from mcp_servers.seo.adapters.dataforseo_client import DataForSeoClient


@patch("httpx.post")
def test_keyword_ideas_posts_basic_auth_and_payload(mock_post: MagicMock) -> None:
    mock_post.return_value.json.return_value = {"tasks": [{"status_code": 20000}]}
    client = DataForSeoClient(login="user@example.com", password="pw")

    result = client.keyword_ideas("agent IA", "fr", 2250)

    assert result == {"tasks": [{"status_code": 20000}]}
    kwargs = mock_post.call_args.kwargs
    assert kwargs["headers"]["Authorization"].startswith("Basic ")
    assert kwargs["json"][0]["keyword"] == "agent IA"


@patch("httpx.post")
def test_serp_analysis_posts_expected_payload(mock_post: MagicMock) -> None:
    mock_post.return_value.json.return_value = {"tasks": []}
    client = DataForSeoClient(login="user@example.com", password="pw")

    client.serp_analysis("agent IA", "fr", 2250)

    payload = mock_post.call_args.kwargs["json"]
    assert payload == [{"keyword": "agent IA", "language_code": "fr", "location_code": 2250}]
