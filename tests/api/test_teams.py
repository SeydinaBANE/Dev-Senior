"""Tests for Microsoft Teams outgoing webhook integration."""

import base64
import hashlib
import hmac
import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch


def _stub_agents() -> None:
    """Injecte des agents factices dans sys.modules pour éviter l'init OpenRouter."""
    for mod_path in (
        "agents.dev_senior.agent",
        "agents.biz_manager.agent",
    ):
        if mod_path not in sys.modules:
            m = ModuleType(mod_path)
            m.agent = MagicMock()  # type: ignore[attr-defined]
            sys.modules[mod_path] = m


_stub_agents()

import pytest  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from api.routes.teams import _parse_agent_and_text, router  # noqa: E402


def _make_sessions() -> MagicMock:
    mock = MagicMock()
    mock.get_history = AsyncMock(return_value=[])
    mock.set_history = AsyncMock()
    mock.delete_session = AsyncMock()
    return mock


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.state.sessions = _make_sessions()
    return TestClient(app)


_KEY = base64.b64encode(b"test-teams-key-32-bytes-padding!!").decode()


def _teams_auth(body: bytes, key: str = _KEY) -> str:
    key_bytes = base64.b64decode(key)
    sig = base64.b64encode(hmac.new(key_bytes, body, hashlib.sha256).digest()).decode()
    return f"HMAC {sig}"


# ── /teams/health ─────────────────────────────────────────────────────────────


def test_health_not_configured(client: TestClient) -> None:
    with patch("api.routes.teams._WEBHOOK_KEY", ""):
        r = client.get("/teams/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["teams_configured"] is False


def test_health_configured(client: TestClient) -> None:
    with patch("api.routes.teams._WEBHOOK_KEY", _KEY):
        r = client.get("/teams/health")
    assert r.json()["teams_configured"] is True


# ── _parse_agent_and_text ─────────────────────────────────────────────────────


def test_parse_dev_senior_mention() -> None:
    agent, text = _parse_agent_and_text("@dev-senior explique ce code")
    assert agent == "dev-senior"
    assert text == "explique ce code"


def test_parse_biz_manager_mention() -> None:
    agent, text = _parse_agent_and_text("@biz-manager analyse ce lead")
    assert agent == "biz-manager"
    assert text == "analyse ce lead"


def test_parse_no_mention_defaults_dev_senior() -> None:
    agent, text = _parse_agent_and_text("comment fonctionne cet algo ?")
    assert agent == "dev-senior"
    assert "comment fonctionne" in text


def test_parse_strips_html_tags() -> None:
    agent, text = _parse_agent_and_text("<at>DevSenior</at> <b>explique</b> ce code")
    assert agent == "dev-senior"
    assert "<" not in text
    assert "explique" in text


# ── /teams/message ────────────────────────────────────────────────────────────


def test_message_empty_text(client: TestClient) -> None:
    with patch("api.routes.teams._WEBHOOK_KEY", ""):
        r = client.post("/teams/message", json={"type": "message", "text": ""})
    assert r.status_code == 200
    assert "vide" in r.json()["text"].lower()


def test_message_routes_to_dev_senior(client: TestClient) -> None:
    mock_result = MagicMock()
    mock_result.data = "Réponse Dev Senior"
    mock_result.all_messages = MagicMock(return_value=[])

    with patch("api.routes.teams._WEBHOOK_KEY", ""):
        with patch("api.routes.teams.dev_agent") as mock_agent:
            mock_agent.run = AsyncMock(return_value=mock_result)
            r = client.post(
                "/teams/message",
                json={
                    "type": "message",
                    "text": "@dev-senior explique ce code",
                    "conversation": {"id": "conv-1"},
                },
            )

    assert r.status_code == 200
    assert r.json()["text"] == "Réponse Dev Senior"
    assert r.json()["type"] == "message"


def test_message_routes_to_biz_manager(client: TestClient) -> None:
    mock_result = MagicMock()
    mock_result.data = "Réponse Biz Manager"
    mock_result.all_messages = MagicMock(return_value=[])

    with patch("api.routes.teams._WEBHOOK_KEY", ""):
        with patch("api.routes.teams.biz_agent") as mock_agent:
            mock_agent.run = AsyncMock(return_value=mock_result)
            r = client.post(
                "/teams/message",
                json={
                    "type": "message",
                    "text": "@biz-manager analyse ce lead",
                    "conversation": {"id": "conv-2"},
                },
            )

    assert r.status_code == 200
    assert r.json()["text"] == "Réponse Biz Manager"


def test_message_saves_session_history(client: TestClient) -> None:
    mock_result = MagicMock()
    mock_result.data = "Réponse."
    mock_result.all_messages = MagicMock(return_value=[])

    with patch("api.routes.teams._WEBHOOK_KEY", ""):
        with patch("api.routes.teams.dev_agent") as mock_agent:
            mock_agent.run = AsyncMock(return_value=mock_result)
            client.post(
                "/teams/message",
                json={"type": "message", "text": "question", "conversation": {"id": "conv-42"}},
            )

    client.app.state.sessions.set_history.assert_awaited_once()
    call_args = client.app.state.sessions.set_history.call_args[0]
    assert call_args[0] == "teams:conv-42"


def test_message_reset_deletes_session(client: TestClient) -> None:
    with patch("api.routes.teams._WEBHOOK_KEY", ""):
        r = client.post(
            "/teams/message",
            json={"type": "message", "text": "reset", "conversation": {"id": "conv-99"}},
        )

    assert r.status_code == 200
    assert "réinitialisée" in r.json()["text"]
    client.app.state.sessions.delete_session.assert_awaited_once_with("teams:conv-99")


def test_message_invalid_signature_rejected(client: TestClient) -> None:
    with patch("api.routes.teams._WEBHOOK_KEY", _KEY):
        r = client.post(
            "/teams/message",
            headers={"authorization": "HMAC invalide=="},
            json={"type": "message", "text": "test"},
        )
    assert r.status_code == 403


def test_message_missing_auth_rejected(client: TestClient) -> None:
    with patch("api.routes.teams._WEBHOOK_KEY", _KEY):
        r = client.post(
            "/teams/message",
            json={"type": "message", "text": "test"},
        )
    assert r.status_code == 403


def test_message_agent_error_returns_message(client: TestClient) -> None:
    with patch("api.routes.teams._WEBHOOK_KEY", ""):
        with patch("api.routes.teams.dev_agent") as mock_agent:
            mock_agent.run = AsyncMock(side_effect=RuntimeError("oops"))
            r = client.post(
                "/teams/message",
                json={"type": "message", "text": "question", "conversation": {"id": "conv-err"}},
            )

    assert r.status_code == 200
    assert "oops" in r.json()["text"]
