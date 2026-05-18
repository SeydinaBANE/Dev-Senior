# Dev-Senior — Instructions pour Claude Code

## Contexte du projet

Ce dépôt contient deux agents IA internes déployés sur Mac mini M4 :

- **Dev Senior** (`agents/dev_senior/`) : assistant technique permanent. Connaît la codebase via RAG (Qdrant). Accès GitHub via MCP.
- **Business Manager** (`agents/biz_manager/`) : assistant non-technique. Accès Google Workspace, CRM HubSpot, SEO via MCP. Mémoire des interactions.

**Stack** : Pydantic AI · OpenRouter · Qdrant · PostgreSQL · FastAPI · React (Vite) · n8n · Langfuse · MCP custom

## Structure critique

```
agents/
  dev_senior/    ← agent.py, prompts.py, __main__.py
  biz_manager/   ← agent.py, prompts.py, __main__.py

mcp_servers/
  github/        ← accès repo, issues, PRs
  google_workspace/ ← Gmail, Calendar, Drive
  crm/           ← HubSpot
  seo/           ← outils SEO

api/             ← FastAPI : auth.py, db.py (asyncpg), main.py, sessions.py
  routes/        ← biz_manager.py, dev_senior.py (endpoints par agent)

memory/          ← couche mémoire vectorielle
  embeddings.py  ← génération embeddings via OpenRouter
  store.py       ← interface Qdrant
  dev_senior/    ← indexer.py, retriever.py (RAG codebase)
  biz_manager/   ← context.py (mémoire interactions)
  vector_store/  ← données Qdrant locales (ne pas committer)

observability/   ← langfuse_config.py, evals/ (qualité + dérive)

workflows/
  n8n/           ← 5 JSONs importables (tous avec header X-API-Key)

frontend/        ← React + Vite + TypeScript + Tailwind (port 5173)
  src/
    api/         ← clients fetch vers l'API
    components/  ← composants React
    hooks/       ← hooks personnalisés

infra/
  docker/        ← docker-compose (Qdrant + PostgreSQL + n8n)
  deploy/        ← start/stop/healthcheck/launchd + init.sql
  ollama/        ← vestige pre-migration (ne plus utiliser, stack = OpenRouter)

tests/
  agents/        ← test_smoke.py (TestModel Pydantic AI, pas d'appel réseau)
  mcp_servers/   ← test_github.py

docs/            ← guide_dev_senior.md, guide_biz_manager.md

.github/
  workflows/     ← ci.yml (lint + tests), deploy.yml (déploiement)
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
| `LANGFUSE_PUBLIC_KEY` | Clé publique Langfuse (tracing) |
| `LANGFUSE_SECRET_KEY` | Clé secrète Langfuse |
| `LANGFUSE_HOST` | URL Langfuse (défaut : cloud.langfuse.com) |
| `DOCS_ENABLED=false` | Désactiver Swagger en prod |

## Décisions architecturales

- **Pydantic AI** : type-safe, multi-provider, s'intègre nativement avec Langfuse via traces manuelles
- **OpenRouter** : une seule clé pour tous les modèles (Qwen, Llama, embeddings)
- **Qdrant** : base vectorielle prod-ready avec dashboard HTTP (`http://localhost:6333/dashboard`)
- **PostgreSQL + asyncpg** : sessions persistantes avec TTL 60 min, pool de connexions géré dans le lifespan FastAPI
- **MCPServerStdio** : MCP servers démarrés une fois au lancement via `agent.run_mcp_servers()`
- **React + Vite** : frontend découplé, dev proxy vers l'API sur :8080, build statique pour la prod
- **Vite proxy** : `/dev-senior` et `/biz-manager` proxifiés vers `http://localhost:8080` en dev
- **Langfuse** : chaque appel agent crée un `trace` (input/output). Scores LLM-as-judge via `eval_quality.py`. Dashboard sur `cloud.langfuse.com`
