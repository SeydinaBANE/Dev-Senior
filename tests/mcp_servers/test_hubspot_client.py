"""
Tests de l'adapter HubSpotClient — traduction méthode -> appel httpx.
"""

from unittest.mock import MagicMock, patch

from mcp_servers.crm.adapters.hubspot_client import HUBSPOT_BASE, HubSpotClient


def _mock_response(json_data: dict) -> MagicMock:
    r = MagicMock()
    r.json.return_value = json_data
    return r


@patch("httpx.post")
def test_search_contacts_returns_results_list(mock_post: MagicMock) -> None:
    mock_post.return_value = _mock_response({"results": [{"id": "1"}]})
    client = HubSpotClient(api_key="test-key")

    results = client.search_contacts("alice")

    assert results == [{"id": "1"}]
    kwargs = mock_post.call_args.kwargs
    assert kwargs["headers"]["Authorization"] == "Bearer test-key"


@patch("httpx.get")
def test_get_contact_returns_properties_dict(mock_get: MagicMock) -> None:
    mock_get.return_value = _mock_response({"properties": {"firstname": "Bob"}})
    client = HubSpotClient(api_key="test-key")

    result = client.get_contact("42")

    assert result == {"firstname": "Bob"}
    assert f"{HUBSPOT_BASE}/crm/v3/objects/contacts/42" in mock_get.call_args.args[0]


@patch("httpx.post")
def test_create_contact_returns_id(mock_post: MagicMock) -> None:
    mock_post.return_value = _mock_response({"id": "99"})
    client = HubSpotClient(api_key="test-key")

    result = client.create_contact("bob@example.com", "Bob", "Durand", "Acme")

    assert result == "99"
    payload = mock_post.call_args.kwargs["json"]
    assert payload["properties"]["email"] == "bob@example.com"


@patch("httpx.post")
def test_list_deals_adds_filter_when_stage_given(mock_post: MagicMock) -> None:
    mock_post.return_value = _mock_response({"results": []})
    client = HubSpotClient(api_key="test-key")

    client.list_deals("closedwon")

    payload = mock_post.call_args.kwargs["json"]
    assert payload["filterGroups"][0]["filters"][0]["value"] == "closedwon"


@patch("httpx.post")
def test_list_deals_no_filter_when_no_stage(mock_post: MagicMock) -> None:
    mock_post.return_value = _mock_response({"results": []})
    client = HubSpotClient(api_key="test-key")

    client.list_deals("")

    payload = mock_post.call_args.kwargs["json"]
    assert "filterGroups" not in payload


@patch("httpx.post")
def test_create_note_posts_association_to_contact(mock_post: MagicMock) -> None:
    mock_post.return_value = _mock_response({"id": "note-1"})
    client = HubSpotClient(api_key="test-key")

    client.create_note("42", "contenu de la note")

    payload = mock_post.call_args.kwargs["json"]
    assert payload["associations"][0]["to"]["id"] == "42"
    assert payload["properties"]["hs_note_body"] == "contenu de la note"
