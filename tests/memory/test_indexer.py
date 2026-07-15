"""
Tests de l'indexeur de codebase.
VectorStore injecté en fake (aucun appel réseau ni Qdrant réel) ; embed_batch patché.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from memory.dev_senior import indexer as idx
from memory.dev_senior.retriever import CodebaseRepository
from memory.ports import VectorHit, VectorStore

runner = CliRunner()


class FakeVectorStore(VectorStore):
    def __init__(self) -> None:
        self.scroll_by_source: dict[str, str] = {}  # rel_path -> hash
        self.deleted: list[dict] = []
        self.upserted: list[tuple[str, list]] = []
        self.ensured = False

    def ensure_collection(self, name: str, size: int = 1536) -> None:
        self.ensured = True

    def count(self, name: str) -> int:
        return len(self.scroll_by_source)

    def upsert(self, name: str, points: list) -> None:
        self.upserted.append((name, points))
        for p in points:
            self.scroll_by_source[p.payload["source"]] = p.payload["hash"]

    def search(self, name, query_vector, *, limit, score_threshold=None, query_filter=None):
        return []

    def scroll(self, name, *, filter, limit):
        source = filter.get("source")
        if source in self.scroll_by_source:
            return [
                VectorHit(id=1, payload={"source": source, "hash": self.scroll_by_source[source]})
            ]
        return []

    def delete(self, name, *, filter) -> None:
        self.deleted.append(filter)
        self.scroll_by_source.pop(filter.get("source"), None)


def _write_file(tmp_path: Path, name: str, content: str) -> None:
    (tmp_path / name).write_text(content, encoding="utf-8")


@patch("memory.dev_senior.indexer.embed_batch", return_value=[[0.1] * 1536])
def test_index_new_file_is_upserted(mock_embed_batch: MagicMock, tmp_path: Path) -> None:
    _write_file(tmp_path, "a.py", "print('hello')")
    store = FakeVectorStore()

    with patch(
        "memory.dev_senior.indexer.CodebaseRepository", return_value=CodebaseRepository(store=store)
    ):
        result = runner.invoke(idx.app, [str(tmp_path)])

    assert result.exit_code == 0
    assert len(store.upserted) == 1
    assert "a.py" in store.scroll_by_source


@patch("memory.dev_senior.indexer.embed_batch", return_value=[[0.1] * 1536])
def test_index_unchanged_file_is_skipped(mock_embed_batch: MagicMock, tmp_path: Path) -> None:
    _write_file(tmp_path, "a.py", "print('hello')")
    store = FakeVectorStore()
    content_hash = idx.file_hash("print('hello')")
    store.scroll_by_source["a.py"] = content_hash

    with patch(
        "memory.dev_senior.indexer.CodebaseRepository", return_value=CodebaseRepository(store=store)
    ):
        result = runner.invoke(idx.app, [str(tmp_path)])

    assert result.exit_code == 0
    assert len(store.upserted) == 0
    assert len(store.deleted) == 0


@patch("memory.dev_senior.indexer.embed_batch", return_value=[[0.1] * 1536])
def test_index_changed_file_deletes_then_reindexes(
    mock_embed_batch: MagicMock, tmp_path: Path
) -> None:
    _write_file(tmp_path, "a.py", "print('changed')")
    store = FakeVectorStore()
    store.scroll_by_source["a.py"] = "old-hash-different-from-new-content"

    with patch(
        "memory.dev_senior.indexer.CodebaseRepository", return_value=CodebaseRepository(store=store)
    ):
        result = runner.invoke(idx.app, [str(tmp_path)])

    assert result.exit_code == 0
    assert store.deleted == [{"source": "a.py"}]
    assert len(store.upserted) == 1


@patch("memory.dev_senior.indexer.embed_batch", return_value=[[0.1] * 1536])
def test_index_force_reindexes_unchanged_file(mock_embed_batch: MagicMock, tmp_path: Path) -> None:
    _write_file(tmp_path, "a.py", "print('hello')")
    store = FakeVectorStore()
    content_hash = idx.file_hash("print('hello')")
    store.scroll_by_source["a.py"] = content_hash

    with patch(
        "memory.dev_senior.indexer.CodebaseRepository", return_value=CodebaseRepository(store=store)
    ):
        result = runner.invoke(idx.app, [str(tmp_path), "--force"])

    assert result.exit_code == 0
    assert len(store.upserted) == 1
    assert len(store.deleted) == 0  # pas d'existing_hash consulté en mode --force
