"""Tests for Slack slash command integration."""
import hashlib
import hmac
import sys
import time
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
from api.routes.slack import router, _run_agent_and_reply  # noqa: E402


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


def _slack_headers(body: str, secret: str = "test-secret") -> dict:
    ts = str(int(time.time()))
    base = f"v0:{ts}:{body}"
    sig = "v0=" + hmac.new(secret.encode(), base.encode(), hashlib.sha256).hexdigest()
    return {"x-slack-request-timestamp": ts, "x-slack-signature": sig}


# ── /slack/health ─────────────────────────────────────────────────────────────

def test_health_not_configured(client: TestClient) -> None:
    with patch("api.routes.slack._SIGNING_SECRET", ""):
        r = client.get("/slack/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["slack_configured"] is False


def test_health_configured(client: TestClient) -> None:
    with patch("api.routes.slack._SIGNING_SECRET", "some-secret"):
        r = client.get("/slack/health")
    assert r.json()["slack_configured"] is True


# ── /slack/command ─────────────────────────────────────────────────────────────

def test_command_empty_text(client: TestClient) -> None:
    with patch("api.routes.slack._SIGNING_SECRET", ""):
        r = client.post(
            "/slack/command",
            data={"command": "/dev-senior", "text": "", "response_url": "http://x", "user_name": "bob"},
        )
    assert r.status_code == 200
    assert r.json()["response_type"] == "ephemeral"


def test_command_dev_senior_acks_immediately(client: TestClient) -> None:
    with patch("api.routes.slack._SIGNING_SECRET", ""):
        r = client.post(
            "/slack/command",
            data={
                "command": "/dev-senior",
                "text": "how do I refactor this?",
                "response_url": "http://hooks.slack.com/x",
                "user_name": "alice",
                "channel_id": "C123",
                "user_id": "U456",
            },
        )
    assert r.status_code == 200
    body = r.json()
    assert body["response_type"] == "in_channel"
    assert "alice" in body["text"]
    assert "how do I refactor this?" in body["text"]


def test_command_biz_manager_acks_immediately(client: TestClient) -> None:
    with patch("api.routes.slack._SIGNING_SECRET", ""):
        r = client.post(
            "/slack/command",
            data={
                "command": "/biz-manager",
                "text": "analyse ce lead",
                "response_url": "http://hooks.slack.com/y",
                "user_name": "carol",
                "channel_id": "C123",
                "user_id": "U789",
            },
        )
    assert r.status_code == 200
    assert r.json()["response_type"] == "in_channel"


def test_command_reset_deletes_session(client: TestClient) -> None:
    with patch("api.routes.slack._SIGNING_SECRET", ""):
        r = client.post(
            "/slack/command",
            data={
                "command": "/dev-senior",
                "text": "reset",
                "response_url": "http://hooks.slack.com/x",
                "user_name": "alice",
                "channel_id": "C123",
                "user_id": "U456",
            },
        )
    assert r.status_code == 200
    assert r.json()["response_type"] == "ephemeral"
    assert "réinitialisée" in r.json()["text"]
    client.app.state.sessions.delete_session.assert_awaited_once_with("slack:C123:U456")


def test_command_invalid_signature_rejected(client: TestClient) -> None:
    with patch("api.routes.slack._SIGNING_SECRET", "real-secret"):
        r = client.post(
            "/slack/command",
            headers={"x-slack-request-timestamp": str(int(time.time())), "x-slack-signature": "v0=bad"},
            data={"command": "/dev-senior", "text": "test", "response_url": "http://x", "user_name": "eve"},
        )
    assert r.status_code == 403


def test_command_expired_timestamp_rejected(client: TestClient) -> None:
    old_ts = str(int(time.time()) - 600)  # 10 minutes ago
    with patch("api.routes.slack._SIGNING_SECRET", "real-secret"):
        r = client.post(
            "/slack/command",
            headers={"x-slack-request-timestamp": old_ts, "x-slack-signature": "v0=whatever"},
            data={"command": "/dev-senior", "text": "test", "response_url": "http://x", "user_name": "eve"},
        )
    assert r.status_code == 403


# ── _run_agent_and_reply ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_agent_posts_to_response_url() -> None:
    mock_result = MagicMock()
    mock_result.data = "Voici ma réponse."
    mock_result.all_messages = MagicMock(return_value=[])

    mock_sessions = _make_sessions()

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_ctx.post = AsyncMock()

    with patch("api.routes.slack.dev_agent") as mock_agent:
        mock_agent.run = AsyncMock(return_value=mock_result)
        with patch("httpx.AsyncClient", return_value=mock_ctx):
            await _run_agent_and_reply(
                "dev-senior", "ma question", "http://hooks.slack.com/z",
                mock_sessions, "slack:C123:U456",
            )

    mock_ctx.post.assert_awaited_once()
    payload = mock_ctx.post.call_args[1]["json"]
    assert payload["text"] == "Voici ma réponse."
    assert payload["response_type"] == "in_channel"


@pytest.mark.asyncio
async def test_run_agent_saves_history_after_run() -> None:
    mock_result = MagicMock()
    mock_result.data = "Réponse."
    mock_result.all_messages = MagicMock(return_value=[])

    mock_sessions = _make_sessions()

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_ctx.post = AsyncMock()

    with patch("api.routes.slack.dev_agent") as mock_agent:
        mock_agent.run = AsyncMock(return_value=mock_result)
        with patch("httpx.AsyncClient", return_value=mock_ctx):
            await _run_agent_and_reply(
                "dev-senior", "question", "http://hooks.slack.com/z",
                mock_sessions, "slack:C123:U456",
            )

    mock_sessions.set_history.assert_awaited_once()
    call_args = mock_sessions.set_history.call_args[0]
    assert call_args[0] == "slack:C123:U456"


@pytest.mark.asyncio
async def test_run_agent_posts_error_on_exception() -> None:
    mock_sessions = _make_sessions()

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_ctx.post = AsyncMock()

    with patch("api.routes.slack.dev_agent") as mock_agent:
        mock_agent.run = AsyncMock(side_effect=RuntimeError("boom"))
        with patch("httpx.AsyncClient", return_value=mock_ctx):
            await _run_agent_and_reply(
                "dev-senior", "question", "http://hooks.slack.com/z",
                mock_sessions, "slack:C123:U456",
            )

    payload = mock_ctx.post.call_args[1]["json"]
    assert ":warning:" in payload["text"]
    assert "boom" in payload["text"]
