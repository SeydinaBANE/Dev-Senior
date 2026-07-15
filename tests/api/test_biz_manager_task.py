"""Tests for POST /biz-manager/task (one-shot n8n endpoint, no session)."""

import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch


def _stub_memory() -> None:
    for mod_path, attr in (
        ("memory.biz_manager.context", "retrieve_context"),
        ("memory.biz_manager.context", "save_interaction"),
    ):
        if mod_path not in sys.modules:
            m = ModuleType(mod_path)
            setattr(m, attr, MagicMock(return_value=""))
            sys.modules[mod_path] = m


_stub_memory()

import pytest  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from api.auth import require_api_key  # noqa: E402
from api.routes.biz_manager import router  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_api_key] = lambda: None
    app.state.agents = MagicMock()
    return TestClient(app)


def test_task_returns_agent_result(client: TestClient) -> None:
    mock_result = MagicMock()
    mock_result.data = "Résultat de la tâche."
    client.app.state.agents.biz_manager.run = AsyncMock(return_value=mock_result)

    with patch("api.routes.biz_manager.save_interaction") as mock_save:
        r = client.post("/biz-manager/task", json={"task": "Analyse ce lead"})

    assert r.status_code == 200
    assert r.json()["result"] == "Résultat de la tâche."
    mock_save.assert_called_once_with("Analyse ce lead", "Résultat de la tâche.")


def test_task_includes_context_in_prompt(client: TestClient) -> None:
    mock_result = MagicMock()
    mock_result.data = "ok"
    client.app.state.agents.biz_manager.run = AsyncMock(return_value=mock_result)

    with patch("api.routes.biz_manager.save_interaction"):
        client.post(
            "/biz-manager/task",
            json={"task": "Rédige un résumé", "context": "Client: Acme"},
        )

    prompt = client.app.state.agents.biz_manager.run.call_args[0][0]
    assert "Client: Acme" in prompt
    assert "Rédige un résumé" in prompt


def test_task_without_context_uses_task_as_prompt(client: TestClient) -> None:
    mock_result = MagicMock()
    mock_result.data = "ok"
    client.app.state.agents.biz_manager.run = AsyncMock(return_value=mock_result)

    with patch("api.routes.biz_manager.save_interaction"):
        client.post("/biz-manager/task", json={"task": "Juste la tâche"})

    prompt = client.app.state.agents.biz_manager.run.call_args[0][0]
    assert prompt == "Juste la tâche"
