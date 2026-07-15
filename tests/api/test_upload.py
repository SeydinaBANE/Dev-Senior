"""Tests for POST /{agent}/upload endpoints."""

import io
import sys
from types import ModuleType
from unittest.mock import MagicMock


def _stub_memory() -> None:
    for mod_path, attr in (
        ("memory.dev_senior.retriever", "retrieve_context"),
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
from api.routes.biz_manager import router as biz_router  # noqa: E402
from api.routes.dev_senior import router as dev_router  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(dev_router)
    app.include_router(biz_router)
    app.dependency_overrides[require_api_key] = lambda: None
    app.state.agents = MagicMock()
    return TestClient(app)


def test_upload_text_file(client: TestClient) -> None:
    content = b"def hello():\n    return 42"
    r = client.post(
        "/dev-senior/upload",
        files={"file": ("hello.py", io.BytesIO(content), "text/plain")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["filename"] == "hello.py"
    assert "def hello" in data["text"]
    assert data["size_chars"] > 0


def test_upload_biz_manager(client: TestClient) -> None:
    content = b"Revenue: 100k"
    r = client.post(
        "/biz-manager/upload",
        files={"file": ("report.txt", io.BytesIO(content), "text/plain")},
    )
    assert r.status_code == 200
    assert "Revenue" in r.json()["text"]


def test_upload_unsupported_format(client: TestClient) -> None:
    r = client.post(
        "/dev-senior/upload",
        files={"file": ("image.png", io.BytesIO(b"\x89PNG"), "image/png")},
    )
    assert r.status_code == 422
    assert "png" in r.json()["detail"].lower()


def test_upload_large_file_truncated(client: TestClient) -> None:
    big = b"a" * 25_000
    r = client.post(
        "/dev-senior/upload",
        files={"file": ("big.txt", io.BytesIO(big), "text/plain")},
    )
    assert r.status_code == 200
    data = r.json()
    assert "tronqué" in data["text"]
    assert data["size_chars"] <= 20_500


def test_upload_csv(client: TestClient) -> None:
    csv = b"name,score\nalice,95\nbob,87"
    r = client.post(
        "/dev-senior/upload",
        files={"file": ("data.csv", io.BytesIO(csv), "text/csv")},
    )
    assert r.status_code == 200
    assert "alice" in r.json()["text"]
