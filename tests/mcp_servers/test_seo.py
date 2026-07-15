"""
Tests des outils SEO — mock Google Search Console et DataForSEO pour éviter les appels réseau.
"""

from unittest.mock import MagicMock, patch

from mcp_servers.seo import server as seo

# ── top_queries ───────────────────────────────────────────────────────────────


@patch("mcp_servers.seo.server.SITE_URL", "https://example.com")
@patch("mcp_servers.seo.adapters.search_console_client.get_credentials")
@patch("mcp_servers.seo.adapters.search_console_client.build")
def test_top_queries_returns_results(mock_build: MagicMock, mock_creds: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.searchanalytics().query().execute.return_value = {
        "rows": [
            {"keys": ["agent IA"], "clicks": 120, "impressions": 1000, "ctr": 0.12, "position": 3.5}
        ]
    }
    result = seo.top_queries("2026-05-01", "2026-05-18")
    assert "agent IA" in result
    assert "120" in result


@patch("mcp_servers.seo.server.SITE_URL", "https://example.com")
@patch("mcp_servers.seo.adapters.search_console_client.get_credentials")
@patch("mcp_servers.seo.adapters.search_console_client.build")
def test_top_queries_empty(mock_build: MagicMock, mock_creds: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.searchanalytics().query().execute.return_value = {"rows": []}
    result = seo.top_queries("2026-05-01", "2026-05-18")
    assert "Aucune" in result


@patch("mcp_servers.seo.server.SITE_URL", "")
def test_top_queries_no_site_url() -> None:
    result = seo.top_queries("2026-05-01", "2026-05-18")
    assert "SEARCH_CONSOLE_SITE_URL" in result


# ── page_performance ──────────────────────────────────────────────────────────


@patch("mcp_servers.seo.server.SITE_URL", "https://example.com")
@patch("mcp_servers.seo.adapters.search_console_client.get_credentials")
@patch("mcp_servers.seo.adapters.search_console_client.build")
def test_page_performance_returns_results(mock_build: MagicMock, mock_creds: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.searchanalytics().query().execute.return_value = {
        "rows": [
            {
                "keys": ["agent senior"],
                "clicks": 50,
                "impressions": 400,
                "ctr": 0.125,
                "position": 5.2,
            }
        ]
    }
    result = seo.page_performance("https://example.com/blog", "2026-05-01", "2026-05-18")
    assert "agent senior" in result
    assert "50" in result


@patch("mcp_servers.seo.server.SITE_URL", "https://example.com")
@patch("mcp_servers.seo.adapters.search_console_client.get_credentials")
@patch("mcp_servers.seo.adapters.search_console_client.build")
def test_page_performance_empty(mock_build: MagicMock, mock_creds: MagicMock) -> None:
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.searchanalytics().query().execute.return_value = {"rows": []}
    result = seo.page_performance("https://example.com/404", "2026-05-01", "2026-05-18")
    assert "Aucune" in result


@patch("mcp_servers.seo.server.SITE_URL", "")
def test_page_performance_no_site_url() -> None:
    result = seo.page_performance("https://example.com/blog", "2026-05-01", "2026-05-18")
    assert "SEARCH_CONSOLE_SITE_URL" in result


# ── keyword_ideas ─────────────────────────────────────────────────────────────


@patch("mcp_servers.seo.server.DATAFORSEO_LOGIN", "user@example.com")
@patch("httpx.post")
def test_keyword_ideas_returns_results(mock_post: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "tasks": [
            {
                "status_code": 20000,
                "result": [
                    {
                        "items": [
                            {
                                "keyword": "agent IA",
                                "keyword_info": {"search_volume": 500},
                                "keyword_difficulty": 30,
                            }
                        ]
                    }
                ],
            }
        ]
    }
    mock_post.return_value = mock_response
    result = seo.keyword_ideas("intelligence artificielle")
    assert "agent IA" in result
    assert "500" in result


@patch("mcp_servers.seo.server.DATAFORSEO_LOGIN", "")
def test_keyword_ideas_no_credentials() -> None:
    result = seo.keyword_ideas("intelligence artificielle")
    assert "DATAFORSEO" in result


@patch("mcp_servers.seo.server.DATAFORSEO_LOGIN", "user@example.com")
@patch("httpx.post")
def test_keyword_ideas_api_error(mock_post: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "tasks": [{"status_code": 40000, "status_message": "Bad Request"}]
    }
    mock_post.return_value = mock_response
    result = seo.keyword_ideas("test")
    assert "Erreur" in result


# ── serp_analysis ─────────────────────────────────────────────────────────────


@patch("mcp_servers.seo.server.DATAFORSEO_LOGIN", "user@example.com")
@patch("httpx.post")
def test_serp_analysis_returns_results(mock_post: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "tasks": [
            {
                "status_code": 20000,
                "result": [
                    {
                        "items": [
                            {
                                "type": "organic",
                                "rank_absolute": 1,
                                "title": "Les agents IA en 2026",
                                "url": "https://example.com/agents",
                            }
                        ]
                    }
                ],
            }
        ]
    }
    mock_post.return_value = mock_response
    result = seo.serp_analysis("agent IA")
    assert "Les agents IA en 2026" in result
    assert "example.com" in result


@patch("mcp_servers.seo.server.DATAFORSEO_LOGIN", "user@example.com")
@patch("httpx.post")
def test_serp_analysis_filters_non_organic(mock_post: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "tasks": [
            {
                "status_code": 20000,
                "result": [
                    {
                        "items": [
                            {
                                "type": "paid",
                                "rank_absolute": 1,
                                "title": "Pub",
                                "url": "https://ads.example.com",
                            },
                            {
                                "type": "organic",
                                "rank_absolute": 2,
                                "title": "Résultat organique",
                                "url": "https://blog.example.com",
                            },
                        ]
                    }
                ],
            }
        ]
    }
    mock_post.return_value = mock_response
    result = seo.serp_analysis("agent IA")
    assert "Résultat organique" in result
    assert "Pub" not in result


@patch("mcp_servers.seo.server.DATAFORSEO_LOGIN", "")
def test_serp_analysis_no_credentials() -> None:
    result = seo.serp_analysis("agent IA")
    assert "DATAFORSEO" in result
