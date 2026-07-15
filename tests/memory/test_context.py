"""
Tests de la mémoire contextuelle Business Manager.
VectorStore injecté en fake (aucun appel réseau) ; embed patché.
"""

from unittest.mock import MagicMock, patch

from memory.biz_manager import context as bc
from memory.biz_manager.context import BizContextRepository
from memory.ports import VectorHit, VectorStore


class FakeVectorStore(VectorStore):
    def __init__(self) -> None:
        self.points_count = 0
        self.search_results: list[VectorHit] = []
        self.search_calls: list[dict] = []
        self.upserted: list[tuple[str, list]] = []

    def ensure_collection(self, name: str, size: int = 1536) -> None:
        pass

    def count(self, name: str) -> int:
        return self.points_count

    def upsert(self, name: str, points: list) -> None:
        self.upserted.append((name, points))

    def search(self, name, query_vector, *, limit, score_threshold=None, query_filter=None):
        self.search_calls.append({"query_filter": query_filter})
        return self.search_results

    def scroll(self, name, *, filter, limit):
        return []

    def delete(self, name, *, filter) -> None:
        pass


@patch("memory.biz_manager.context.embed", return_value=[0.1] * 1536)
def test_save_note_returns_uuid(mock_embed: MagicMock) -> None:
    store = FakeVectorStore()
    repo = BizContextRepository(store=store)

    note_id = repo.save_note("Brief campagne Q3", category="brief")

    assert len(note_id) == 36
    assert store.upserted[0][0] == "biz_context"


@patch("memory.biz_manager.context.embed", return_value=[0.1] * 1536)
def test_retrieve_returns_none_when_collection_empty(mock_embed: MagicMock) -> None:
    store = FakeVectorStore()
    store.points_count = 0
    repo = BizContextRepository(store=store)

    assert repo.retrieve("query") is None


@patch("memory.biz_manager.context.embed", return_value=[0.1] * 1536)
def test_retrieve_returns_empty_string_when_no_hits(mock_embed: MagicMock) -> None:
    store = FakeVectorStore()
    store.points_count = 5
    store.search_results = []
    repo = BizContextRepository(store=store)

    assert repo.retrieve("query") == ""


@patch("memory.biz_manager.context.embed", return_value=[0.1] * 1536)
def test_retrieve_formats_hits(mock_embed: MagicMock) -> None:
    store = FakeVectorStore()
    store.points_count = 1
    store.search_results = [
        VectorHit(
            id="1",
            payload={
                "category": "client",
                "created_at": "2026-05-18T10:00:00+00:00",
                "text": "Acme préfère les emails courts",
            },
            score=0.8,
        )
    ]
    repo = BizContextRepository(store=store)

    result = repo.retrieve("préférences Acme")

    assert "--- Contexte mémorisé ---" in result
    assert "Acme préfère les emails courts" in result


@patch("memory.biz_manager.context.embed", return_value=[0.1] * 1536)
def test_retrieve_filters_by_category(mock_embed: MagicMock) -> None:
    store = FakeVectorStore()
    store.points_count = 2
    repo = BizContextRepository(store=store)

    repo.retrieve("query", category="deadline")

    assert store.search_calls[-1]["query_filter"] == {"category": "deadline"}


# ── Comportement historique : collection vide court-circuite le fallback partagé ──


def test_retrieve_context_skips_shared_when_collection_empty() -> None:
    with (
        patch.object(bc._repo, "retrieve", return_value=None) as mock_retrieve,
        patch("memory.biz_manager.context.retrieve_shared") as mock_shared,
    ):
        result = bc.retrieve_context("query")

        assert result == ""
        mock_retrieve.assert_called_once()
        mock_shared.assert_not_called()


def test_retrieve_context_checks_shared_when_no_hits_but_not_empty() -> None:
    with (
        patch.object(bc._repo, "retrieve", return_value=""),
        patch("memory.biz_manager.context.retrieve_shared", return_value="--- shared ---"),
    ):
        result = bc.retrieve_context("query")

    assert result == "--- shared ---"


def test_retrieve_context_combines_blocks() -> None:
    with (
        patch.object(bc._repo, "retrieve", return_value="--- notes ---"),
        patch("memory.biz_manager.context.retrieve_shared", return_value="--- shared ---"),
    ):
        result = bc.retrieve_context("query")

    assert result == "--- notes ---\n--- shared ---"


def test_save_interaction_saves_note_and_shared() -> None:
    with (
        patch.object(bc._repo, "save_note", return_value="id") as mock_save_note,
        patch("memory.biz_manager.context.save_shared") as mock_save_shared,
    ):
        bc.save_interaction("Question client ?", "Réponse détaillée", topic="onboarding")

    mock_save_note.assert_called_once()
    mock_save_shared.assert_called_once()
    assert mock_save_shared.call_args.kwargs["source_agent"] == "biz_manager"
