# Dev-Senior — Instructions pour Claude Code

## Contexte du projet

Ce dépôt contient deux agents IA internes déployés sur Mac mini M4 :

- **Dev Senior** (`agents/dev_senior/`) : assistant technique permanent. Connaît la codebase via RAG (Qdrant). Accès GitHub via MCP.
- **Business Manager** (`agents/biz_manager/`) : assistant non-technique. Accès Google Workspace, CRM HubSpot, SEO via MCP. Mémoire des interactions.

Les deux agents partagent une collection Qdrant `shared` pour les contextes cross-agent.

**Stack** : Pydantic AI · OpenRouter · Qdrant · PostgreSQL · Redis · FastAPI · React (Vite) · n8n · Langfuse · Slack · Teams · MCP custom

## Structure critique

```
agents/
  dev_senior/    ← agent.py, prompts.py, __main__.py
  biz_manager/   ← agent.py, prompts.py, __main__.py
  config.py      ← openrouter_model(), dev_senior_model(), biz_manager_model()

mcp_servers/
  github/           ← list_prs, get_pr_diff, read_file, search_code, create_issue…
  google_workspace/ ← Gmail, Calendar, Drive
  crm/              ← HubSpot (contacts, deals, notes)
  seo/              ← Search Console + DataForSEO

api/
  auth.py           ← require_api_key (open en dev si AGENTS_API_KEY absent)
  db.py             ← pool asyncpg + get_pool()
  main.py           ← App + CORS + lifespan (MCP + sessions + Langfuse)
  sessions.py       ← SessionStore (ABC) → RedisSessionStore | PostgresSessionStore
  metrics_store.py  ← métriques in-memory thread-safe (P50/P95, taux d'erreur)
  routes/
    dev_senior.py   ← POST /dev-senior/chat (JSON) | /chat/stream (SSE) | /reset | GET /health
    biz_manager.py  ← POST /biz-manager/chat (JSON) | /chat/stream (SSE) | /task | /reset | GET /health
    metrics.py      ← GET /metrics (latence + qualité, auth requise)
    slack.py        ← POST /slack/command (slash commands /dev-senior /biz-manager) — sessions par canal+user (slack:{channel_id}:{user_id}), mot-clé "reset"
    teams.py        ← POST /teams/message (outgoing webhook, routage par @mention) — sessions par conversation (teams:{conversation_id}), mot-clé "reset"

memory/
  embeddings.py  ← génération embeddings via OpenRouter
  store.py       ← client Qdrant partagé (singleton)
  dev_senior/    ← indexer.py, retriever.py (RAG codebase, collection "codebase")
  biz_manager/   ← context.py (mémoire interactions, collection "biz_context")
  shared/        ← memory.py (save_shared, retrieve_shared, collection "shared")
  vector_store/  ← données Qdrant locales (ne pas committer)

observability/
  langfuse_config.py     ← configure_observability(), get_langfuse(), flush()
  evals/
    eval_quality.py      ← LLM-as-judge (OpenRouter) + scores Langfuse
    eval_drift.py        ← détection dérive vs baseline
    cron_eval.py         ← orchestrateur quotidien (traces Langfuse → scores → log)

workflows/
  n8n/           ← 5 JSONs importables (tous avec header X-API-Key)

frontend/
  .env.example   ← template : VITE_API_KEY, VITE_API_URL (committer)
  src/
    api/         ← agents.ts : fetch avec VITE_API_KEY + VITE_API_URL base
    components/  ← Sidebar, ChatWindow, MessageBubble, InputBar, MetricsDashboard
    hooks/       ← useChat.ts

infra/
  docker/        ← docker-compose (Qdrant + PostgreSQL + Redis + n8n)
  deploy/        ← start/stop/healthcheck/launchd plist (API + eval cron) + init.sql
  ollama/        ← vestige pre-migration (ne plus utiliser, stack = OpenRouter)

tests/
  agents/        ← test_smoke.py (TestModel Pydantic AI, pas d'appel réseau)
  mcp_servers/   ← test_github.py, test_crm.py, test_seo.py, test_google_workspace.py
  memory/        ← test_shared.py
  observability/ ← test_evals.py
  api/           ← test_sessions.py, test_slack.py, test_teams.py, test_streaming.py

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
make frontend-env       # créer frontend/.env.local depuis le template
make frontend           # Vite dev server (port 5173)
make frontend-build     # build de production (bakes VITE_API_KEY dans le bundle)
make serve-prod         # build frontend + API prod (frontend servi sur /app)

make index-codebase     # indexer le repo dans Qdrant (mémoire Dev Senior)

make check              # lint + mypy + pytest
make test               # pytest seul
make lint               # ruff check
make format             # ruff format
make typecheck          # mypy agents/ api/ memory/ observability/

make eval-quality       # éval LLM-as-judge
make eval-drift         # comparer aux métriques baseline
make eval-set-baseline  # fixer la baseline
make install-eval-cron  # installer le cron d'évaluation quotidienne (launchd)
make logs               # tail -f logs/api.log
make install-service    # installer le service launchd API (démarrage au boot)
```

## Conventions de code

- Python 3.11+, type hints stricts, `mypy --strict`
- Pydantic AI pour les agents : `Agent(model=..., system_prompt=..., mcp_servers=[...])`
- MCP servers : `FastMCP` de `mcp.server.fastmcp`, `if __name__ == "__main__": mcp.run()`
- Sessions : `SessionStore.create()` dans le lifespan → `app.state.sessions`. Les routes utilisent `request.app.state.sessions` (duck-typed, Redis ou PostgreSQL selon `REDIS_URL`)
- Sérialisation Pydantic AI : `ModelMessagesTypeAdapter.dump_python(..., mode="json")` pour JSON
- Tests : `TestModel` de Pydantic AI pour les smoke tests (pas d'appel réseau). Pour les routes Slack/Teams/streaming, injecter des agents factices via `sys.modules` avant l'import (pattern dans `tests/api/test_slack.py`). Pour les endpoints streaming, mocker `agent.run_stream()` avec un `@asynccontextmanager` qui yield un objet dont `stream_text()` est un générateur async (pattern dans `tests/api/test_streaming.py`)
- Pas de commentaires évidents — seulement les "pourquoi" non-triviaux
- Slack : lire `await request.body()` AVANT tout `Form()` parsing pour éviter "Stream consumed" — parser le form-encoded body manuellement avec `urllib.parse.parse_qs`

## Sécurité — règles absolues

- Ne jamais hardcoder de clés API → toujours via `os.getenv()`
- `credentials.json`, `token.json`, `.env`, `frontend/.env.local` → gitignorés, ne jamais committer
- Tous les endpoints API utilisent `Depends(require_api_key)` sauf `/health`
- `AGENTS_API_KEY` doit être défini en prod (générer avec `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`)
- Le pre-commit bloque automatiquement les commits avec secrets détectés
- Slack : vérifier `X-Slack-Signature` HMAC-SHA256 + drift temporel 5 min (`_verify_signature` dans `api/routes/slack.py`)
- Teams : vérifier `Authorization: HMAC <sig>` SHA256 (`_verify_signature` dans `api/routes/teams.py`)

## Variables d'environnement clés

| Variable | Usage |
|---|---|
| `OPENROUTER_API_KEY` | Clé OpenRouter (tous les LLMs + embeddings) |
| `AGENTS_API_KEY` | Auth de l'API interne |
| `DATABASE_URL` | PostgreSQL (sessions persistantes — fallback si REDIS_URL absent) |
| `REDIS_URL` | Sessions Redis (optionnel — ex: `redis://localhost:6379/0`) |
| `SESSION_TTL_SECONDS` | TTL sessions (défaut : 3600) |
| `QDRANT_HOST` / `QDRANT_PORT` | Mémoire vectorielle |
| `GITHUB_TOKEN` | MCP GitHub (scopes: `repo`) |
| `GOOGLE_CREDENTIALS_FILE` | OAuth Google Workspace |
| `CRM_API_KEY` | HubSpot Private App Token |
| `SLACK_SIGNING_SECRET` | Vérification HMAC slash commands Slack (vide = open en dev) |
| `TEAMS_WEBHOOK_KEY` | Vérification HMAC outgoing webhook Teams (vide = open en dev) |
| `LANGFUSE_PUBLIC_KEY` | Clé publique Langfuse (tracing) |
| `LANGFUSE_SECRET_KEY` | Clé secrète Langfuse |
| `LANGFUSE_HOST` | URL Langfuse (défaut : cloud.langfuse.com) |
| `DOCS_ENABLED=false` | Désactiver Swagger en prod |

## Décisions architecturales

- **Pydantic AI** : type-safe, multi-provider, s'intègre nativement avec Langfuse via traces manuelles
- **OpenRouter** : une seule clé pour tous les modèles (Qwen, Llama, embeddings)
- **Qdrant** : base vectorielle prod-ready avec dashboard HTTP (`http://localhost:6333/dashboard`). 3 collections : `codebase` (RAG Dev Senior), `biz_context` (mémoire Biz Manager), `shared` (cross-agent)
- **SessionStore (ABC)** : factory `SessionStore.create()` sélectionne Redis si `REDIS_URL` est défini, sinon PostgreSQL. Zéro changement côté routes. `RedisSessionStore` utilise des hashes Redis avec `EXPIRE` natif ; `PostgresSessionStore` wrape asyncpg avec cleanup TTL manuel. `set_history` utilise un UPSERT (`INSERT ... ON CONFLICT DO UPDATE`) pour créer les sessions externes (Slack/Teams) au premier appel sans passer par `new_session`
- **MCPServerStdio** : MCP servers démarrés une fois au lancement via `agent.run_mcp_servers()`
- **React + Vite** : frontend découplé, dev proxy vers l'API sur :8080, build statique pour la prod (`base: '/app/'`). En prod, `StaticFiles(html=True)` sur `/app` sert le SPA avec fallback. `VITE_API_URL` permet de déployer le frontend sur un hôte différent
- **Streaming SSE** : `POST /chat/stream` utilise `agent.run_stream(delta=True)` et retourne `StreamingResponse(media_type="text/event-stream")`. Format : `event: session` → deltas JSON-encodés → `data: [DONE]` (ou `event: error`). Le JSON-encoding des deltas évite les problèmes de caractères spéciaux dans le protocole SSE. Session et `save_interaction()` sauvegardés après le stream, pas pendant. `X-Accel-Buffering: no` désactive le buffering nginx. Les endpoints `/chat` (JSON) coexistent comme fallback pour n8n
- **Slack** : ack immédiat (< 3s) + `BackgroundTask` pour le vrai appel agent + POST à `response_url`. Body lu brut pour HMAC avant parsing manuel du form. Session key = `slack:{channel_id}:{user_id}` — historique chargé/sauvegardé dans `_run_agent_and_reply`. Mot-clé `reset` traité de façon synchrone avant le background task.
- **Teams** : réponse synchrone (Teams n'a pas de timeout strict), routage par regex sur le préfixe `@mention`, nettoyage HTML des balises Teams. `TeamsMessage.conversation: dict[str, str]` porte le `conversation.id`. Session key = `teams:{conversation_id}`. Mot-clé `reset` vide la session avant de retourner.
- **Métriques** : `_AgentStore` in-memory avec `threading.Lock`, snapshot `statistics.quantiles` pour P50/P95. `GET /metrics` agrège runtime + dernier fichier JSON d'évaluation
- **Eval cron** : launchd plist `com.agents.eval.plist`, 2h du matin, écrit un log JSON quotidien dans `logs/`
- **Langfuse** : chaque appel agent crée un `trace` (input/output). Scores LLM-as-judge via `eval_quality.py`. Dashboard sur `cloud.langfuse.com`
