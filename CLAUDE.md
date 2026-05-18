# Dev-Senior — Instructions pour Claude Code

## Contexte du projet

Ce dépôt contient deux agents IA internes déployés sur Mac mini M4 :

- **Dev Senior** (`agents/dev_senior/`) : assistant technique permanent. Connaît la codebase via RAG (Qdrant). Accès GitHub via MCP.
- **Business Manager** (`agents/biz_manager/`) : assistant non-technique. Accès Google Workspace, CRM HubSpot, SEO via MCP. Mémoire des interactions.

**Stack** : Pydantic AI · OpenRouter · Qdrant · PostgreSQL · FastAPI · React (Vite) · n8n · Logfire · MCP custom

## Structure critique

```
agents/          ← Pydantic AI agents (modèle, prompt, mémoire)
mcp_servers/     ← Serveurs MCP (GitHub, Google WS, CRM, SEO)
api/             ← FastAPI : auth.py, db.py (asyncpg), main.py, routes/, sessions.py
memory/          ← Qdrant : embeddings (OpenRouter), indexer, retriever
observability/   ← logfire_config.py, evals/ (qualité + dérive)
workflows/n8n/   ← 5 JSONs importables (tous avec header X-API-Key)
frontend/        ← React + Vite + TypeScript + Tailwind (port 5173)
infra/docker/    ← docker-compose (Qdrant + PostgreSQL + n8n)
infra/deploy/    ← start/stop/healthcheck/launchd + init.sql
```

## Commandes essentielles

```bash
make setup              # venv + pip install + pre-commit install
make start              # tout démarrer (Docker + API)
make stop               # tout arrêter
make healthcheck        # vérifier Qdrant, PostgreSQL, API, n8n

make dev-senior         # lancer l'agent Dev Senior (terminal)
make biz-manager        # lancer l'agent Business Manager (terminal)
make api                # lancer l'API FastAPI (port 8080)
make n8n                # ouvrir n8n (port 5678)

make frontend-install   # npm install dans frontend/
make frontend           # Vite dev server (port 5173)
make frontend-build     # build de production

make index-codebase     # indexer le repo dans Qdrant (mémoire Dev Senior)

make check              # lint + mypy + pytest
make test               # pytest seul
make lint               # ruff check
make format             # ruff format
make typecheck          # mypy agents/ api/ memory/ observability/

make eval-quality       # éval LLM-as-judge
make eval-drift         # comparer aux métriques baseline
make logs               # tail -f logs/api.log
make install-service    # installer le service launchd (démarrage au boot)
```

## Conventions de code

- Python 3.11+, type hints stricts, `mypy --strict`
- Pydantic AI pour les agents : `Agent(model=..., system_prompt=..., mcp_servers=[...])`
- MCP servers : `FastMCP` de `mcp.server.fastmcp`, `if __name__ == "__main__": mcp.run()`
- Sessions : asyncpg + PostgreSQL (pool dans `app.state.pool`, dépendance `get_pool(request)`)
- Sérialisation Pydantic AI : `ModelMessagesTypeAdapter.dump_python(..., mode="json")` pour JSON
- Tests : `TestModel` de Pydantic AI pour les smoke tests (pas d'appel réseau)
- Pas de commentaires évidents — seulement les "pourquoi" non-triviaux

## Sécurité — règles absolues

- Ne jamais hardcoder de clés API → toujours via `os.getenv()`
- `credentials.json`, `token.json`, `.env` → gitignorés, ne jamais committer
- Tous les endpoints API utilisent `Depends(require_api_key)` sauf `/health`
- `AGENTS_API_KEY` doit être défini en prod (générer avec `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`)
- Le pre-commit bloque automatiquement les commits avec secrets détectés

## Variables d'environnement clés

| Variable | Usage |
|---|---|
| `OPENROUTER_API_KEY` | Clé OpenRouter (tous les LLMs + embeddings) |
| `AGENTS_API_KEY` | Auth de l'API interne |
| `DATABASE_URL` | PostgreSQL (sessions persistantes) |
| `QDRANT_HOST` / `QDRANT_PORT` | Mémoire vectorielle |
| `GITHUB_TOKEN` | MCP GitHub (scopes: `repo`) |
| `GOOGLE_CREDENTIALS_FILE` | OAuth Google Workspace |
| `CRM_API_KEY` | HubSpot Private App Token |
| `DOCS_ENABLED=false` | Désactiver Swagger en prod |

## Décisions architecturales

- **Pydantic AI** : type-safe, multi-provider, natif Logfire
- **OpenRouter** : une seule clé pour tous les modèles (Qwen, Llama, embeddings)
- **Qdrant** : base vectorielle prod-ready avec dashboard HTTP (`http://localhost:6333/dashboard`)
- **PostgreSQL + asyncpg** : sessions persistantes avec TTL 60 min, pool de connexions géré dans le lifespan FastAPI
- **MCPServerStdio** : MCP servers démarrés une fois au lancement via `agent.run_mcp_servers()`
- **React + Vite** : frontend découplé, dev proxy vers l'API sur :8080, build statique pour la prod
- **Vite proxy** : `/dev-senior` et `/biz-manager` proxifiés vers `http://localhost:8080` en dev
