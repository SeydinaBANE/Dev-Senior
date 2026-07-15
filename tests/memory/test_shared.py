"""
Tests de la mémoire partagée entre agents.
VectorStore injecté en fake (aucun appel réseau) ; embed patché.
"""

from unittest.mock import MagicMock, patch

from memory.ports import VectorHit, VectorStore
from memory.shared import memory as sm
from memory.shared.memory import SharedMemoryRepository


class FakeVectorStore(VectorStore):
    def __init__(self) -> None:
        self.collections: set[str] = set()
        self.upserted: list[tuple[str, list]] = []
        self.search_results: list[VectorHit] = []
        self.search_calls: list[dict] = []
        self.points_count = 0

    def ensure_collection(self, name: str, size: int = 1536) -> None:
        self.collections.add(name)

    def count(self, name: str) -> int:
        return self.points_count

    def upsert(self, name: str, points: list) -> None:
        self.upserted.append((name, points))

    def search(self, name, query_vector, *, limit, score_threshold=None, query_filter=None):
        self.search_calls.append(
            {"limit": limit, "score_threshold": score_threshold, "query_filter": query_filter}
        )
        return self.search_results

    def scroll(self, name, *, filter, limit):
        return []

    def delete(self, name, *, filter) -> None:
        pass


def _hit(text: str, source_agent: str, category: str = "general") -> VectorHit:
    return VectorHit(
        id="1",
        payload={
            "text": text,
            "source_agent": source_agent,
            "category": category,
            "created_at": "2026-05-18T10:00:00+00:00",
        },
        score=0.9,
    )


@patch("memory.shared.memory.embed", return_value=[0.1] * 1536)
def test_save_returns_uuid(mock_embed: MagicMock) -> None:
    store = FakeVectorStore()
    repo = SharedMemoryRepository(store=store)

    note_id = repo.save(
        "Livraison Acme avant juin", source_agent="biz_manager", category="deadline"
    )

    assert len(note_id) == 36  # format UUID
    assert len(store.upserted) == 1
    assert store.upserted[0][0] == "shared"


@patch("memory.shared.memory.embed", return_value=[0.1] * 1536)
def test_retrieve_returns_results(mock_embed: MagicMock) -> None:
    store = FakeVectorStore()
    store.points_count = 2
    store.search_results = [
        _hit("Client Acme veut livraison avant juin", "biz_manager", "deadline"),
        _hit("Stack technique : OpenRouter + Qdrant", "dev_senior", "decision"),
    ]
    repo = SharedMemoryRepository(store=store)

    result = repo.retrieve("deadline projet")

    assert "Acme" in result
    assert "biz_manager" in result
    assert "dev_senior" in result
    assert "--- Contexte partagé ---" in result


@patch("memory.shared.memory.embed", return_value=[0.1] * 1536)
def test_retrieve_empty_collection(mock_embed: MagicMock) -> None:
    store = FakeVectorStore()
    store.points_count = 0
    repo = SharedMemoryRepository(store=store)

    assert repo.retrieve("quelque chose") == ""


@patch("memory.shared.memory.embed", return_value=[0.1] * 1536)
def test_retrieve_no_match(mock_embed: MagicMock) -> None:
    store = FakeVectorStore()
    store.points_count = 5
    store.search_results = []
    repo = SharedMemoryRepository(store=store)

    assert repo.retrieve("sujet sans correspondance") == ""


@patch("memory.shared.memory.embed", return_value=[0.1] * 1536)
def test_retrieve_filters_by_source_agent(mock_embed: MagicMock) -> None:
    store = FakeVectorStore()
    store.points_count = 3
    store.search_results = [_hit("Info biz uniquement", "biz_manager", "client")]
    repo = SharedMemoryRepository(store=store)

    result = repo.retrieve("info client", source_agent="biz_manager")

    assert "Info biz uniquement" in result
    assert store.search_calls[-1]["query_filter"] == {"source_agent": "biz_manager"}


@patch("memory.shared.memory.embed", return_value=[0.1] * 1536)
def test_retrieve_no_filter_when_no_source_agent(mock_embed: MagicMock) -> None:
    store = FakeVectorStore()
    store.points_count = 2
    store.search_results = []
    repo = SharedMemoryRepository(store=store)

    repo.retrieve("query")

    assert store.search_calls[-1]["query_filter"] is None


# ── Tests de façade : save_shared/retrieve_shared délèguent bien au repo ──────


def test_save_shared_delegates_to_default_repo() -> None:
    with patch.object(sm._repo, "save", return_value="note-id") as mock_save:
        result = sm.save_shared("contenu", source_agent="dev_senior")
        assert result == "note-id"
        mock_save.assert_called_once_with("contenu", "dev_senior", "general", "")


def test_retrieve_shared_delegates_to_default_repo() -> None:
    with patch.object(sm._repo, "retrieve", return_value="contexte") as mock_retrieve:
        result = sm.retrieve_shared("query", top_k=2, source_agent="biz_manager")
        assert result == "contexte"
        mock_retrieve.assert_called_once_with("query", 2, "biz_manager")
