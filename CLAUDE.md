# Dev-Senior — Instructions pour Claude Code

## Contexte du projet

Ce dépôt contient deux agents IA internes déployés sur Mac mini M4 :

- **Dev Senior** (`agents/dev_senior/`) : assistant technique permanent. Connaît la codebase via RAG (ChromaDB). Accès GitHub via MCP.
- **Business Manager** (`agents/biz_manager/`) : assistant non-technique. Accès Google Workspace, CRM HubSpot, SEO via MCP. Mémoire des interactions.

**Stack** : Pydantic AI · Ollama (Docker) · ChromaDB · FastAPI · n8n · Logfire · MCP custom

## Structure critique

```
agents/          ← Pydantic AI agents (modèle, prompt, mémoire)
mcp_servers/     ← Serveurs MCP (GitHub, Google WS, CRM, SEO)
api/             ← FastAPI : auth.py (X-API-Key), main.py (CORS+lifespan), routes/
memory/          ← ChromaDB : embeddings, indexer, retriever
observability/   ← logfire_config.py, evals/ (qualité + dérive)
workflows/n8n/   ← 5 JSONs importables (tous avec header X-API-Key)
infra/docker/    ← docker-compose (Ollama+ChromaDB+n8n), pull-models.sh
infra/deploy/    ← start/stop/healthcheck/launchd
```

## Commandes essentielles

```bash
make setup              # venv + pip install + pre-commit install
make start              # tout démarrer (Docker + API)
make stop               # tout arrêter
make healthcheck        # vérifier Ollama, ChromaDB, API, n8n

make dev-senior         # lancer l'agent Dev Senior (local)
make dev-senior-cloud   # lancer avec Claude API (USE_CLOUD=true)
make biz-manager        # lancer l'agent Business Manager
make api                # lancer l'API FastAPI (port 8080)
make n8n                # ouvrir n8n (port 5678)

make index-codebase     # indexer le repo dans ChromaDB (mémoire Dev Senior)
make models             # télécharger les modèles dans Ollama Docker

make check              # lint + mypy + pytest
make test               # pytest seul
make lint               # ruff check
make format             # ruff format
make typecheck          # mypy agents/ api/ memory/ observability/

make eval-quality       # éval LLM-as-judge (nécessite un fichier samples)
make eval-drift         # comparer aux métriques baseline
make eval-set-baseline  # définir la baseline courante
make logs               # tail -f logs/api.log
make install-service    # installer le service launchd (démarrage au boot)
```

## Conventions de code

- Python 3.11+, type hints stricts, `mypy --strict`
- Pydantic AI pour les agents : `Agent(model=..., system_prompt=..., mcp_servers=[...])`
- MCP servers : `FastMCP` de `mcp.server.fastmcp`, `if __name__ == "__main__": mcp.run()`
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
| `ANTHROPIC_API_KEY` | Claude API |
| `AGENTS_API_KEY` | Auth de l'API interne |
| `GITHUB_TOKEN` | MCP GitHub (scopes: `repo`) |
| `GOOGLE_CREDENTIALS_FILE` | OAuth Google Workspace |
| `CRM_API_KEY` | HubSpot Private App Token |
| `USE_CLOUD=true` | Utiliser Claude API au lieu d'Ollama |
| `DOCS_ENABLED=false` | Désactiver Swagger en prod |

## Décisions architecturales

- **Pydantic AI** choisi pour : type-safe, multi-provider (local/cloud sans changer le code), natif Logfire
- **Docker pour Ollama** : CPU uniquement sur Mac (pas de Metal dans Docker Desktop) — acceptable pour le PoC, native Ollama si perf insuffisante
- **MCPServerStdio** : les MCP servers sont des sous-processus stdio → démarrés une fois au lancement de l'API via `agent.run_mcp_servers()`
- **Sessions en mémoire** : TTL 60 min, Redis si scale nécessaire
- **nomic-embed-text** : modèle d'embedding local via Ollama, cohérent avec la stack
