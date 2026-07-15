"""
Tests du retriever de contexte codebase.
VectorStore injecté en fake (aucun appel réseau) ; embed patché.
"""

from unittest.mock import MagicMock, patch

from memory.dev_senior.retriever import CodebaseRepository
from memory.ports import VectorHit, VectorPoint, VectorStore


class FakeVectorStore(VectorStore):
    def __init__(self) -> None:
        self.points_count = 0
        self.search_results: list[VectorHit] = []
        self.scroll_results: list[VectorHit] = []
        self.deleted: list[dict] = []
        self.upserted: list[tuple[str, list]] = []

    def ensure_collection(self, name: str, size: int = 1536) -> None:
        pass

    def count(self, name: str) -> int:
        return self.points_count

    def upsert(self, name: str, points: list) -> None:
        self.upserted.append((name, points))

    def search(self, name, query_vector, *, limit, score_threshold=None, query_filter=None):
        return self.search_results

    def scroll(self, name, *, filter, limit):
        return self.scroll_results

    def delete(self, name, *, filter) -> None:
        self.deleted.append(filter)


@patch("memory.dev_senior.retriever.embed", return_value=[0.1] * 1536)
def test_retrieve_empty_collection_returns_empty_string(mock_embed: MagicMock) -> None:
    store = FakeVectorStore()
    store.points_count = 0
    repo = CodebaseRepository(store=store)

    assert repo.retrieve("comment marche l'auth") == ""


@patch("memory.dev_senior.retriever.embed", return_value=[0.1] * 1536)
def test_retrieve_no_hits_returns_empty_string(mock_embed: MagicMock) -> None:
    store = FakeVectorStore()
    store.points_count = 3
    store.search_results = []
    repo = CodebaseRepository(store=store)

    assert repo.retrieve("query sans résultat") == ""


@patch("memory.dev_senior.retriever.embed", return_value=[0.1] * 1536)
def test_retrieve_formats_hits_into_prompt_block(mock_embed: MagicMock) -> None:
    store = FakeVectorStore()
    store.points_count = 2
    store.search_results = [
        VectorHit(id=1, payload={"source": "api/main.py", "text": "app = FastAPI()"}, score=0.91)
    ]
    repo = CodebaseRepository(store=store)

    result = repo.retrieve("point d'entrée FastAPI")

    assert "--- Contexte codebase pertinent ---" in result
    assert "api/main.py" in result
    assert "91%" in result
    assert "app = FastAPI()" in result
    assert "--- Fin du contexte ---" in result


def test_existing_hash_returns_hash_when_present() -> None:
    store = FakeVectorStore()
    store.scroll_results = [VectorHit(id=1, payload={"source": "a.py", "hash": "abc123"})]
    repo = CodebaseRepository(store=store)

    assert repo.existing_hash("a.py") == "abc123"


def test_existing_hash_returns_none_when_absent() -> None:
    store = FakeVectorStore()
    store.scroll_results = []
    repo = CodebaseRepository(store=store)

    assert repo.existing_hash("a.py") is None


def test_delete_file_forwards_filter() -> None:
    store = FakeVectorStore()
    repo = CodebaseRepository(store=store)

    repo.delete_file("a.py")

    assert store.deleted == [{"source": "a.py"}]


def test_upsert_chunks_forwards_points() -> None:
    store = FakeVectorStore()
    repo = CodebaseRepository(store=store)
    points = [VectorPoint(id=1, vector=[0.1], payload={"source": "a.py"})]

    repo.upsert_chunks(points)

    assert store.upserted == [("codebase", points)]


def test_retrieve_context_combines_codebase_and_shared_blocks() -> None:
    with (
        patch("memory.dev_senior.retriever._repo") as mock_repo,
        patch("memory.dev_senior.retriever.retrieve_shared", return_value="--- shared ---"),
    ):
        mock_repo.retrieve.return_value = "--- codebase ---"
        from memory.dev_senior.retriever import retrieve_context

        result = retrieve_context("query")

    assert result == "--- codebase ---\n--- shared ---"


def test_retrieve_context_empty_when_both_empty() -> None:
    with (
        patch("memory.dev_senior.retriever._repo") as mock_repo,
        patch("memory.dev_senior.retriever.retrieve_shared", return_value=""),
    ):
        mock_repo.retrieve.return_value = ""
        from memory.dev_senior.retriever import retrieve_context

        result = retrieve_context("query")

    assert result == ""
