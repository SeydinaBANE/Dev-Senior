"""
Tests des outils CRM (HubSpot) — mock httpx pour éviter les appels réseau.
"""

from unittest.mock import MagicMock, patch

from mcp_servers.crm import server as crm


def _mock_post(json_data: dict) -> MagicMock:
    r = MagicMock()
    r.json.return_value = json_data
    return r


def _mock_get(json_data: dict) -> MagicMock:
    r = MagicMock()
    r.json.return_value = json_data
    return r


# ── search_contacts ───────────────────────────────────────────────────────────


@patch("mcp_servers.crm.server.CRM_API_KEY", "test-key")
@patch("httpx.post")
def test_search_contacts_returns_results(mock_post: MagicMock) -> None:
    mock_post.return_value = _mock_post(
        {
            "results": [
                {
                    "id": "1",
                    "properties": {
                        "firstname": "Alice",
                        "lastname": "Durand",
                        "email": "alice@example.com",
                        "company": "Acme",
                    },
                }
            ]
        }
    )
    result = crm.search_contacts("alice")
    assert "Alice" in result
    assert "alice@example.com" in result


@patch("mcp_servers.crm.server.CRM_API_KEY", "test-key")
@patch("httpx.post")
def test_search_contacts_empty(mock_post: MagicMock) -> None:
    mock_post.return_value = _mock_post({"results": []})
    result = crm.search_contacts("inconnu")
    assert "Aucun" in result


@patch("mcp_servers.crm.server.CRM_API_KEY", "")
def test_search_contacts_no_key() -> None:
    result = crm.search_contacts("alice")
    assert "CRM_API_KEY" in result


# ── get_contact ───────────────────────────────────────────────────────────────


@patch("mcp_servers.crm.server.CRM_API_KEY", "test-key")
@patch("httpx.get")
def test_get_contact_returns_properties(mock_get: MagicMock) -> None:
    mock_get.return_value = _mock_get(
        {"properties": {"firstname": "Bob", "email": "bob@example.com", "company": "Corp"}}
    )
    result = crm.get_contact("42")
    assert "Bob" in result
    assert "bob@example.com" in result


@patch("mcp_servers.crm.server.CRM_API_KEY", "")
def test_get_contact_no_key() -> None:
    result = crm.get_contact("42")
    assert "CRM_API_KEY" in result


# ── create_contact ────────────────────────────────────────────────────────────


@patch("mcp_servers.crm.server.CRM_API_KEY", "test-key")
@patch("httpx.post")
def test_create_contact_returns_id(mock_post: MagicMock) -> None:
    mock_post.return_value = _mock_post({"id": "99"})
    result = crm.create_contact("new@example.com", "New", "User", "Corp")
    assert "99" in result


@patch("mcp_servers.crm.server.CRM_API_KEY", "")
def test_create_contact_no_key() -> None:
    result = crm.create_contact("new@example.com")
    assert "CRM_API_KEY" in result


# ── list_deals ────────────────────────────────────────────────────────────────


@patch("mcp_servers.crm.server.CRM_API_KEY", "test-key")
@patch("httpx.post")
def test_list_deals_returns_results(mock_post: MagicMock) -> None:
    mock_post.return_value = _mock_post(
        {
            "results": [
                {
                    "id": "10",
                    "properties": {
                        "dealname": "Contrat Acme",
                        "amount": "5000",
                        "dealstage": "closedwon",
                        "closedate": "2026-06-01T00:00:00Z",
                    },
                }
            ]
        }
    )
    result = crm.list_deals()
    assert "Contrat Acme" in result
    assert "5000" in result


@patch("mcp_servers.crm.server.CRM_API_KEY", "test-key")
@patch("httpx.post")
def test_list_deals_empty(mock_post: MagicMock) -> None:
    mock_post.return_value = _mock_post({"results": []})
    result = crm.list_deals()
    assert "Aucune" in result


@patch("mcp_servers.crm.server.CRM_API_KEY", "")
def test_list_deals_no_key() -> None:
    result = crm.list_deals()
    assert "CRM_API_KEY" in result


# ── create_note ───────────────────────────────────────────────────────────────


@patch("mcp_servers.crm.server.CRM_API_KEY", "test-key")
@patch("httpx.post")
def test_create_note_confirms_contact(mock_post: MagicMock) -> None:
    mock_post.return_value = _mock_post({"id": "200"})
    result = crm.create_note("42", "Appel de suivi effectué.")
    assert "42" in result


@patch("mcp_servers.crm.server.CRM_API_KEY", "")
def test_create_note_no_key() -> None:
    result = crm.create_note("42", "Note")
    assert "CRM_API_KEY" in result
