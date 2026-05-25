"""Tests for SSE streaming endpoints (/chat/stream)."""

import json
import sys
from contextlib import asynccontextmanager
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _stub_agents() -> None:
    for mod_path in ("agents.dev_senior.agent", "agents.biz_manager.agent"):
        if mod_path not in sys.modules:
            m = ModuleType(mod_path)
            m.agent = MagicMock()  # type: ignore[attr-defined]
            sys.modules[mod_path] = m


def _stub_memory() -> None:
    for mod_path, attr in (
        ("memory.dev_senior.retriever", "retrieve_context"),
        ("memory.biz_manager.context", "retrieve_context"),
        ("memory.biz_manager.context", "save_interaction"),
    ):
        if mod_path not in sys.modules:
            m = ModuleType(mod_path)
            sys.modules[mod_path] = m
        setattr(sys.modules[mod_path], attr, MagicMock(return_value=""))


_stub_agents()
_stub_memory()

from api.auth import require_api_key  # noqa: E402
from api.routes.biz_manager import router as biz_router  # noqa: E402
from api.routes.dev_senior import router as dev_router  # noqa: E402
from api.sessions import SessionStore  # noqa: E402


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(dev_router)
    app.include_router(biz_router)
    app.dependency_overrides[require_api_key] = lambda: None

    mock_sessions = MagicMock(spec=SessionStore)
    mock_sessions.new_session = AsyncMock(return_value="test-session-id")
    mock_sessions.get_history = AsyncMock(return_value=[])
    mock_sessions.set_history = AsyncMock()
    app.state.sessions = mock_sessions
    return app


@pytest.fixture
def client() -> TestClient:
    return TestClient(_make_app())


def _mock_stream_agent(chunks: list[str]) -> MagicMock:
    """Crée un agent mock dont run_stream() yield les chunks donnés."""

    async def _stream_text(delta: bool = False):
        for chunk in chunks:
            yield chunk

    mock_result = MagicMock()
    mock_result.stream_text = _stream_text
    mock_result.all_messages = MagicMock(return_value=[])

    @asynccontextmanager
    async def _run_stream(*args, **kwargs):
        yield mock_result

    mock_agent = MagicMock()
    mock_agent.run_stream = _run_stream
    return mock_agent


def _parse_sse(raw: str) -> list[dict]:
    """Parse le texte SSE brut en liste d'événements {event, data}."""
    events = []
    for block in raw.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        ev: dict = {}
        for line in block.split("\n"):
            if line.startswith("event: "):
                ev["event"] = line[7:]
            elif line.startswith("data: "):
                ev["data"] = line[6:]
        if ev:
            events.append(ev)
    return events


# ── Dev Senior ────────────────────────────────────────────────────────────────


def test_dev_senior_stream_sends_session_first(client: TestClient) -> None:
    mock_agent = _mock_stream_agent(["Hello", " World"])
    with patch("api.routes.dev_senior.agent", mock_agent):
        with patch("api.routes.dev_senior.retrieve_context", return_value=""):
            r = client.post(
                "/dev-senior/chat/stream",
                json={"message": "test", "session_id": ""},
            )
    assert r.status_code == 200
    events = _parse_sse(r.text)
    assert events[0]["event"] == "session"
    assert events[0]["data"] == "test-session-id"


def test_dev_senior_stream_yields_chunks(client: TestClient) -> None:
    mock_agent = _mock_stream_agent(["Bon", "jour"])
    with patch("api.routes.dev_senior.agent", mock_agent):
        with patch("api.routes.dev_senior.retrieve_context", return_value=""):
            r = client.post(
                "/dev-senior/chat/stream",
                json={"message": "test", "session_id": ""},
            )
    events = _parse_sse(r.text)
    chunks = [
        json.loads(e["data"]) for e in events if e.get("event") is None and e["data"] != "[DONE]"
    ]
    assert chunks == ["Bon", "jour"]


def test_dev_senior_stream_ends_with_done(client: TestClient) -> None:
    mock_agent = _mock_stream_agent(["ok"])
    with patch("api.routes.dev_senior.agent", mock_agent):
        with patch("api.routes.dev_senior.retrieve_context", return_value=""):
            r = client.post(
                "/dev-senior/chat/stream",
                json={"message": "test", "session_id": ""},
            )
    events = _parse_sse(r.text)
    last = events[-1]
    assert last.get("event") is None
    assert last["data"] == "[DONE]"


def test_dev_senior_stream_error_yields_error_event(client: TestClient) -> None:
    @asynccontextmanager
    async def _failing_stream(*args, **kwargs):
        raise RuntimeError("agent down")
        yield  # make it an async generator

    mock_agent = MagicMock()
    mock_agent.run_stream = _failing_stream

    with patch("api.routes.dev_senior.agent", mock_agent):
        with patch("api.routes.dev_senior.retrieve_context", return_value=""):
            r = client.post(
                "/dev-senior/chat/stream",
                json={"message": "test", "session_id": ""},
            )
    assert r.status_code == 200
    events = _parse_sse(r.text)
    error_events = [e for e in events if e.get("event") == "error"]
    assert error_events
    assert "agent down" in json.loads(error_events[0]["data"])


def test_dev_senior_stream_content_type(client: TestClient) -> None:
    mock_agent = _mock_stream_agent([])
    with patch("api.routes.dev_senior.agent", mock_agent):
        with patch("api.routes.dev_senior.retrieve_context", return_value=""):
            r = client.post(
                "/dev-senior/chat/stream",
                json={"message": "test", "session_id": ""},
            )
    assert "text/event-stream" in r.headers["content-type"]


# ── Biz Manager ───────────────────────────────────────────────────────────────


def test_biz_manager_stream_yields_chunks(client: TestClient) -> None:
    mock_agent = _mock_stream_agent(["Super", " idée"])
    with patch("api.routes.biz_manager.agent", mock_agent):
        with patch("api.routes.biz_manager.retrieve_context", return_value=""):
            with patch("api.routes.biz_manager.save_interaction"):
                r = client.post(
                    "/biz-manager/chat/stream",
                    json={"message": "test", "session_id": ""},
                )
    events = _parse_sse(r.text)
    chunks = [
        json.loads(e["data"]) for e in events if e.get("event") is None and e["data"] != "[DONE]"
    ]
    assert chunks == ["Super", " idée"]


def test_biz_manager_stream_calls_save_interaction(client: TestClient) -> None:
    mock_agent = _mock_stream_agent(["Réponse"])
    with patch("api.routes.biz_manager.agent", mock_agent):
        with patch("api.routes.biz_manager.retrieve_context", return_value=""):
            with patch("api.routes.biz_manager.save_interaction") as mock_save:
                client.post(
                    "/biz-manager/chat/stream",
                    json={"message": "ma question", "session_id": ""},
                )
    mock_save.assert_called_once_with("ma question", "Réponse")
