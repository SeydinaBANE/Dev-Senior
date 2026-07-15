"""
Tests de l'adapter QdrantVectorStore — traduction port -> appels qdrant_client.
Client Qdrant injecté en fake, aucun appel réseau.
"""

from unittest.mock import MagicMock

from memory.adapters.qdrant_store import QdrantVectorStore
from memory.ports import VectorHit, VectorPoint


def _make_client() -> MagicMock:
    # Pas de spec=QdrantClient : client.search() est appelé pour préserver le
    # comportement historique (voir memory/shared/memory.py), alors que les
    # versions récentes de qdrant-client exposent query_points() à la place —
    # bug préexistant, hors périmètre de cette migration.
    return MagicMock()


def test_ensure_collection_delegates_to_memory_store() -> None:
    client = _make_client()
    client.get_collections.return_value.collections = []
    store = QdrantVectorStore(client=client)

    store.ensure_collection("codebase", size=1536)

    client.create_collection.assert_called_once()
    assert client.create_collection.call_args.kwargs["collection_name"] == "codebase"


def test_count_returns_points_count() -> None:
    client = _make_client()
    client.get_collection.return_value.points_count = 42
    store = QdrantVectorStore(client=client)

    assert store.count("codebase") == 42


def test_count_returns_zero_when_none() -> None:
    client = _make_client()
    client.get_collection.return_value.points_count = None
    store = QdrantVectorStore(client=client)

    assert store.count("codebase") == 0


def test_upsert_builds_point_structs() -> None:
    client = _make_client()
    store = QdrantVectorStore(client=client)

    store.upsert(
        "shared",
        [VectorPoint(id="abc", vector=[0.1, 0.2], payload={"text": "hello"})],
    )

    client.upsert.assert_called_once()
    kwargs = client.upsert.call_args.kwargs
    assert kwargs["collection_name"] == "shared"
    point = kwargs["points"][0]
    assert point.id == "abc"
    assert point.vector == [0.1, 0.2]
    assert point.payload == {"text": "hello"}


def test_search_translates_hits_and_filter() -> None:
    client = _make_client()
    hit = MagicMock(id="1", payload={"text": "match"}, score=0.9)
    client.search.return_value = [hit]
    store = QdrantVectorStore(client=client)

    results = store.search(
        "codebase",
        [0.1] * 1536,
        limit=5,
        score_threshold=0.7,
        query_filter={"source_agent": "biz_manager"},
    )

    assert results == [VectorHit(id="1", payload={"text": "match"}, score=0.9)]
    kwargs = client.search.call_args.kwargs
    assert kwargs["score_threshold"] == 0.7
    assert kwargs["query_filter"] is not None
    assert kwargs["with_payload"] is True


def test_search_no_filter_when_none() -> None:
    client = _make_client()
    client.search.return_value = []
    store = QdrantVectorStore(client=client)

    store.search("shared", [0.1] * 1536, limit=3)

    assert client.search.call_args.kwargs["query_filter"] is None


def test_scroll_translates_points() -> None:
    client = _make_client()
    point = MagicMock(id=5, payload={"source": "a.py", "hash": "xyz"})
    client.scroll.return_value = ([point], None)
    store = QdrantVectorStore(client=client)

    results = store.scroll("codebase", filter={"source": "a.py"}, limit=1)

    assert len(results) == 1
    assert results[0].id == 5
    assert results[0].payload == {"source": "a.py", "hash": "xyz"}
    assert results[0].score is None
    assert client.scroll.call_args.kwargs["scroll_filter"] is not None


def test_delete_passes_filter_selector() -> None:
    client = _make_client()
    store = QdrantVectorStore(client=client)

    store.delete("codebase", filter={"source": "a.py"})

    client.delete.assert_called_once()
    kwargs = client.delete.call_args.kwargs
    assert kwargs["collection_name"] == "codebase"
    assert kwargs["points_selector"] is not None
