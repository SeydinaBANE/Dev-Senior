"""
Tests de la mémoire partagée entre agents.
Mock Qdrant et embeddings pour éviter tout appel réseau.
"""

from unittest.mock import MagicMock, patch

from memory.shared import memory as sm


def _make_hit(text: str, source_agent: str, category: str = "general") -> MagicMock:
    hit = MagicMock()
    hit.payload = {
        "text": text,
        "source_agent": source_agent,
        "category": category,
        "created_at": "2026-05-18T10:00:00+00:00",
    }
    return hit


@patch("memory.shared.memory.ensure_collection")
@patch("memory.shared.memory.embed", return_value=[0.1] * 1536)
@patch("memory.shared.memory.get_client")
def test_save_shared_returns_uuid(
    mock_client: MagicMock, mock_embed: MagicMock, mock_ensure: MagicMock
) -> None:
    mock_client.return_value = MagicMock()
    note_id = sm.save_shared(
        "Livraison Acme avant juin", source_agent="biz_manager", category="deadline"
    )
    assert len(note_id) == 36  # format UUID
    mock_client.return_value.upsert.assert_called_once()


@patch("memory.shared.memory.ensure_collection")
@patch("memory.shared.memory.embed", return_value=[0.1] * 1536)
@patch("memory.shared.memory.get_client")
def test_retrieve_shared_returns_results(
    mock_client: MagicMock, mock_embed: MagicMock, mock_ensure: MagicMock
) -> None:
    mock_qdrant = MagicMock()
    mock_qdrant.get_collection.return_value.points_count = 2
    mock_qdrant.search.return_value = [
        _make_hit("Client Acme veut livraison avant juin", "biz_manager", "deadline"),
        _make_hit("Stack technique : OpenRouter + Qdrant", "dev_senior", "decision"),
    ]
    mock_client.return_value = mock_qdrant

    result = sm.retrieve_shared("deadline projet")
    assert "Acme" in result
    assert "biz_manager" in result
    assert "dev_senior" in result
    assert "--- Contexte partagé ---" in result


@patch("memory.shared.memory.ensure_collection")
@patch("memory.shared.memory.embed", return_value=[0.1] * 1536)
@patch("memory.shared.memory.get_client")
def test_retrieve_shared_empty_collection(
    mock_client: MagicMock, mock_embed: MagicMock, mock_ensure: MagicMock
) -> None:
    mock_qdrant = MagicMock()
    mock_qdrant.get_collection.return_value.points_count = 0
    mock_client.return_value = mock_qdrant

    result = sm.retrieve_shared("quelque chose")
    assert result == ""


@patch("memory.shared.memory.ensure_collection")
@patch("memory.shared.memory.embed", return_value=[0.1] * 1536)
@patch("memory.shared.memory.get_client")
def test_retrieve_shared_no_match(
    mock_client: MagicMock, mock_embed: MagicMock, mock_ensure: MagicMock
) -> None:
    mock_qdrant = MagicMock()
    mock_qdrant.get_collection.return_value.points_count = 5
    mock_qdrant.search.return_value = []
    mock_client.return_value = mock_qdrant

    result = sm.retrieve_shared("sujet sans correspondance")
    assert result == ""


@patch("memory.shared.memory.ensure_collection")
@patch("memory.shared.memory.embed", return_value=[0.1] * 1536)
@patch("memory.shared.memory.get_client")
def test_retrieve_shared_filters_by_source_agent(
    mock_client: MagicMock, mock_embed: MagicMock, mock_ensure: MagicMock
) -> None:
    mock_qdrant = MagicMock()
    mock_qdrant.get_collection.return_value.points_count = 3
    mock_qdrant.search.return_value = [
        _make_hit("Info biz uniquement", "biz_manager", "client"),
    ]
    mock_client.return_value = mock_qdrant

    result = sm.retrieve_shared("info client", source_agent="biz_manager")
    assert "Info biz uniquement" in result
    # vérifie que le filtre source_agent a bien été passé à Qdrant
    call_kwargs = mock_qdrant.search.call_args.kwargs
    assert call_kwargs["query_filter"] is not None


@patch("memory.shared.memory.ensure_collection")
@patch("memory.shared.memory.embed", return_value=[0.1] * 1536)
@patch("memory.shared.memory.get_client")
def test_retrieve_shared_no_filter_when_no_source_agent(
    mock_client: MagicMock, mock_embed: MagicMock, mock_ensure: MagicMock
) -> None:
    mock_qdrant = MagicMock()
    mock_qdrant.get_collection.return_value.points_count = 2
    mock_qdrant.search.return_value = []
    mock_client.return_value = mock_qdrant

    sm.retrieve_shared("query")
    call_kwargs = mock_qdrant.search.call_args.kwargs
    assert call_kwargs["query_filter"] is None
