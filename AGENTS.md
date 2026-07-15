# AGENTS.md — Dev-Senior

High-signal facts for OpenCode working in this repo.

## Language

Project is written in **French**: system prompts, error messages, docs, Slack/Teams replies. Code is self-documenting (no comments); only non-trivial "why" comments.

## Project structure

Two AI agents (Pydantic AI) sharing a FastAPI HTTP API:

- `agents/dev_senior/` — technical assistant (Qwen 7B), GitHub MCP, RAG on indexed codebase
- `agents/biz_manager/` — non-technical assistant (Llama 8B), Google Workspace / HubSpot / SEO MCPs

Entrypoints:
- CLI: `python -m agents.dev_senior` (or `make dev-senior`)
- HTTP: FastAPI on `:8080` mounted via `api/main.py`

## Running checks (order matters)

```bash
make check    # lint -> typecheck -> test  (sequential)
```

- `make lint` = `ruff check .`
- `make typecheck` = `mypy agents/ memory/ports.py memory/adapters/ --ignore-missing-imports` — `agents/`, `memory/ports.py`, `memory/adapters/` are interface-clean; the rest of `memory/`, plus `api/` and `observability/`, have incomplete stubs for asyncpg/qdrant-client that raise false positives in strict mode
- `make test` = `pytest tests/ -v`

Single test: `.venv/bin/pytest tests/api/test_slack.py::test_reset_keyword -v`

Pytest runs in `asyncio_mode = "auto"` — no `@pytest.mark.asyncio` needed.

## Test patterns (critical to know)

Routes no longer import agent singletons directly — they read `request.app.state.agents.dev_senior` / `.biz_manager` / `.get(name)` (an `AgentRegistry`, see below). Route-level tests inject a fake registry straight into `app.state.agents` instead of patching module attributes:

```python
from unittest.mock import MagicMock

app.state.agents = MagicMock()          # .get("dev-senior") returns a MagicMock agent automatically
# or, to control a specific agent's .run()/.run_stream():
client.app.state.agents.dev_senior = mock_agent
```

Some routes still import `memory.*` functions (`retrieve_context`, `save_interaction`) at module level — those are stubbed in `sys.modules` before import if not already loaded, see `_stub_memory()` in `tests/api/test_streaming.py`/`test_upload.py`. `tests/conftest.py` pre-imports the real `memory.dev_senior.retriever` / `memory.biz_manager.context` / `memory.shared.memory` modules so this stubbing never shadows the real classes (`CodebaseRepository`, etc.) needed by `tests/memory/*` — don't remove that import without checking test collection order doesn't break.

Streaming tests need `@asynccontextmanager` wrapping `agent.run_stream` (see `tests/api/test_streaming.py`). Upload tests use `files={"file": ("name.ext", BytesIO(content), mime)}` with `TestClient`.

Smoke tests (`tests/agents/`) use Pydantic AI `TestModel` — no network calls. `tests/agents/test_registry.py` tests `AgentRegistry` with fake `AgentPort` doubles.

New `memory/` ports/adapters/repositories are tested by injecting a fake `VectorStore` (see `tests/memory/test_qdrant_store.py`, `test_retriever.py`, `test_context.py`, `test_shared.py`, `test_indexer.py`) — no real Qdrant needed.

CI sets fake env vars (`OPENROUTER_API_KEY: test-key-ci`, etc.) — any new env required by code must be added there too.

## Pydantic AI quirks

- `pydantic-ai` is pinned `>=0.4,<1.0` in `pyproject.toml` — 1.x/2.x moved `OpenAIModel` and `MCPServerStdio` to different import paths, breaking `agents/config.py` and `agents/adapters/*` at mypy/import time. There's no lockfile, so CI re-resolves this range on every run — if `mypy`/tests suddenly fail with `attr-defined` errors on `pydantic_ai.*` imports, check whether the pin needs bumping to a newer *compatible* release, not removing.
- `OpenAIModel` requires `provider=OpenAIProvider(base_url=..., api_key=...)` — do NOT pass `base_url`/`api_key` directly to the constructor. See `agents/config.py::openrouter_model()`.
- Serialize message history with `ModelMessagesTypeAdapter.dump_python(messages, mode="json")`, not `.model_dump()`.
- MCP servers started once via `AgentRegistry.run_mcp_servers()` in the FastAPI lifespan (nests `dev_senior` then `biz_manager`).

## Session store

Duck-typed at `request.app.state.sessions` — routes never import the concrete class. `SessionStore.create()` auto-selects Redis (if `REDIS_URL` set) or PostgreSQL.

External integrations use session keys:
- Slack: `slack:{channel_id}:{user_id}`
- Teams: `teams:{conversation_id}`

Keyword `reset` in any text input deletes the session.

## Agent registry

Duck-typed at `request.app.state.agents` — routes never import the concrete `Agent` singletons. `agents/ports.py::AgentPort` is a `Protocol` (structurally satisfied by `pydantic_ai.Agent`, not a wrapper class — one backend, no need for an adapter class). `agents/adapters/{dev_senior,biz_manager}_agent.py::build_agent()` construct the real agent (model, system prompt, MCP servers). `agents/registry.py::AgentRegistry.create()` builds both and is set on `app.state.agents` in the FastAPI lifespan; `.dev_senior` / `.biz_manager` / `.get(name)` are the three ways routes/Slack/Teams consume it.

`agents/dev_senior/agent.py` and `agents/biz_manager/agent.py` still exist as thin module-level singletons (`agent = build_agent()`) — but only the CLI entrypoints (`__main__.py`, `make dev-senior`/`make biz-manager`) import them now. Don't reintroduce a direct `from agents.dev_senior.agent import agent` in `api/`.

## API quirks

- **Slack**: read `await request.body()` BEFORE `Form()` parsing (avoids "Stream consumed"). Parse form body manually with `urllib.parse.parse_qs`. Ack in < 3s, real work in `BackgroundTask`.
- **Teams**: synchronous reply. Strip HTML tags from message text. Defaults to Dev Senior if no `@mention`. Regex routes `@dev-senior` / `@biz-manager`.
- **SSE streaming**: format is `event: session` -> delta chunks (JSON-encoded) -> `data: [DONE]`. `X-Accel-Buffering: no` header set. Session saved AFTER stream, not during.
- **File upload**: stateless — server extracts text (`pypdf` / `python-docx` / UTF-8), returns to client, client includes `document_context` in next chat call. Truncated at 20k chars.
- **Health check** (`/dev-senior/health`, `/biz-manager/health`): no auth required. Used by Railway and healthcheck.sh.
- All other endpoints require `X-API-Key` header (auth disabled in dev if `AGENTS_API_KEY` not set).

## Frontend

- React 18 + Vite + TypeScript + Tailwind.
- `VITE_BASE_PATH=/app/` for self-hosted (FastAPI serves `frontend/dist/` at `/app`). `VITE_BASE_PATH=/` for Vercel.
- `VITE_API_URL` allows pointing to remote API (e.g. Railway). Empty = relative URLs.
- Production frontend is built into `frontend/dist/` and served by FastAPI at `/app`. Dev server on `:5173` proxies API to `:8080`.

## Vector memory (Qdrant)

Three collections: `codebase` (RAG, threshold 0.70, top_k=5), `biz_context` (threshold 0.60), `shared` (threshold 0.65, cross-agent).

`memory/ports.py::VectorStore` (ABC) + `memory/adapters/qdrant_store.py::QdrantVectorStore` isolate business logic (thresholds, filters, prompt formatting) from `qdrant_client` calls — that's the only file (with `memory/store.py`, which just holds the shared client singleton) allowed to import `qdrant_client`/`qdrant_client.models`. Each collection has a repository built on the port: `CodebaseRepository` (`memory/dev_senior/retriever.py`, reused by `indexer.py`), `SharedMemoryRepository` (`memory/shared/memory.py`), `BizContextRepository` (`memory/biz_manager/context.py`). `PayloadFilter = dict[str, str]` (AND-of-equality) covers every filter used today. `BizContextRepository.retrieve()` returns `None` (not `""`) when the collection is empty — a historical quirk that short-circuits the cross-agent `retrieve_shared()` fallback; `CodebaseRepository` doesn't have this early-return, it always checks the shared fallback.

`memory/vector_store/` is gitignored (local Qdrant data). Index with `make index-codebase` (incremental) or `make index-codebase-force` (full reindex).

`qdrant-client` is pinned `>=1.10.0` (the version `query_points()` was introduced) — `QdrantClient.search()` was removed starting 1.16.0, so `memory/adapters/qdrant_store.py::QdrantVectorStore.search()` uses `query_points()` (`response.points`, not a bare list) instead. That's the only place that matters; no other file should call `.search()` directly.

`observability/logfire_config.py` is a deprecated compat shim — import from `langfuse_config` directly.

## Docker image

Multi-stage Dockerfile at `infra/docker/Dockerfile`:
- **Stage 1** (node:20-alpine): builds the Vite frontend → `frontend/dist/`
- **Stage 2** (python:3.11-slim): installs the Python package, copies frontend assets

Built with `docker/build-push-action@v6` for **linux/amd64** and **linux/arm64**. Published to `ghcr.io/<owner>/<repo>` via `.github/workflows/docker.yml` on every push/PR/tag.

Key details:
- Build args: `VITE_BASE_PATH=/app/`, `VITE_API_KEY` (optional, pass as GitHub secret)
- `HEALTHCHECK` hits `/dev-senior/health` every 30s
- Runtime `.env` is NOT in the image — supply via docker-compose or platform env vars
- `QDRANT_HOST` defaults to `localhost` in code, override to `qdrant` in Docker via env

## Deployment

- **Self-hosted (Mac mini M4)**: Docker Compose — `make deploy` pulls image from ghcr.io and restarts the container. `start.sh` / `stop.sh` manage all services via `docker compose`. No more launchd.
- **Cloud (Railway, Fly.io, Render)**: the `Dockerfile` is auto-detected by all platforms. Railway previously used Nixpacks (`railway.toml`) — the Dockerfile takes priority if present. Healthcheck endpoint: `/dev-senior/health`.
- **Frontend cloud (Vercel)**: standalone — `frontend/vercel.json` handles SPA rewrites. Set `VITE_API_URL` to point to the hosted API.
- **Eval cron**: launchd `com.agents.eval.plist`, runs nightly at 2 AM. Not containerized — runs from the venv directly.

## Key env vars (only non-obvious ones)

| Variable | Purpose |
|---|---|
| `OPENROUTER_API_KEY` | Single key for all LLMs + embeddings |
| `AGENTS_API_KEY` | Internal API auth (leave empty in dev) |
| `SLACK_SIGNING_SECRET` | Empty = endpoint open in dev |
| `TEAMS_WEBHOOK_KEY` | Empty = endpoint open in dev |
| `DOCS_ENABLED=false` | Disable Swagger in production |
| `EMBED_MODEL` | Default: `openai/text-embedding-3-small` (dim=1536) |
| `SESSION_TTL_SECONDS` | Default: 3600 (60 min) |
| `CORS_ORIGINS` | Default: ports 5173, 5678, 3000 |
