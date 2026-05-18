# Agents IA Internes — Dev Senior & Business Manager

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Pydantic AI](https://img.shields.io/badge/Pydantic_AI-latest-E92063?style=flat-square&logo=pydantic&logoColor=white)](https://ai.pydantic.dev)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-API-6366F1?style=flat-square&logo=openai&logoColor=white)](https://openrouter.ai)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Qdrant](https://img.shields.io/badge/Qdrant-vector_DB-DC382D?style=flat-square&logo=qdrant&logoColor=white)](https://qdrant.tech)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Langfuse](https://img.shields.io/badge/Langfuse-observabilité-000000?style=flat-square&logo=langfuse&logoColor=white)](https://langfuse.com)
[![n8n](https://img.shields.io/badge/n8n-workflows-EA4B71?style=flat-square&logo=n8n&logoColor=white)](https://n8n.io)
[![CI](https://img.shields.io/github/actions/workflow/status/SeydinaBANE/Dev-Senior/ci.yml?branch=main&style=flat-square&label=CI&logo=github)](https://github.com/SeydinaBANE/Dev-Senior/actions)
[![License](https://img.shields.io/badge/licence-MIT-22C55E?style=flat-square)](LICENSE)

Deux agents IA déployés en interne sur Mac mini M4 pour augmenter la productivité de l'équipe technique et des business managers.

---

## Démarrage rapide

```bash
# 1. Setup (une seule fois)
cp .env.example .env        # remplir OPENROUTER_API_KEY + POSTGRES_PASSWORD
make setup                  # venv + deps + pre-commit

# 2. Démarrer tout l'environnement
make docker-up              # Qdrant + PostgreSQL + n8n
make api                    # FastAPI port 8080

# 3. Ouvrir le frontend
make frontend-install       # npm install (une seule fois)
make frontend               # Vite dev server → http://localhost:5173

# 4. Vérifier que tout tourne
make healthcheck
```

---

## Les deux agents

### Agent Dev Senior
**Utilisateurs :** équipe technique
**Capacités :** développement complexe, architecture, debugging, code reviews, refactoring, documentation
**Modèle :** `qwen/qwen-2.5-coder-7b-instruct` via OpenRouter
**Mémoire :** RAG sur la codebase indexée dans Qdrant

### Agent Business Manager
**Utilisateurs :** business managers, stagiaires
**Capacités :** marketing digital, SEO, réseaux sociaux, contenu, emails, CRM, automatisation
**Modèle :** `meta-llama/llama-3.1-8b-instruct` via OpenRouter
**Mémoire :** historique des interactions mémorisé automatiquement dans Qdrant

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│               React Frontend (Vite, port 5173)              │
│         Dev Senior (vert) │ Business Manager (bleu)         │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP (proxy Vite en dev)
┌────────────────────────▼────────────────────────────────────┐
│         FastAPI (port 8080) — API interne sécurisée         │
│              Auth : X-API-Key · CORS : localhost             │
│              Sessions : asyncpg → PostgreSQL                │
└──────────┬──────────────────────────────────────────────────┘
           │ Pydantic AI
┌──────────▼──────────────────────────────────────────────────┐
│                   Agents (Pydantic AI)                      │
│  ┌────────────────────┐       ┌───────────────────────┐     │
│  │    Dev Senior      │       │   Business Manager    │     │
│  │ qwen-2.5-coder:7b  │       │   llama-3.1-8b        │     │
│  └────────┬───────────┘       └──────────┬────────────┘     │
└───────────┼──────────────────────────────┼──────────────────┘
            │             MCP              │
┌───────────▼──────────────────────────────▼──────────────────┐
│                    MCP Servers (custom)                      │
│       GitHub    Google Workspace    CRM (HubSpot)    SEO    │
└──────────────────────────────────────────────────────────────┘
            │
┌───────────▼──────────────────────────────────────────────────┐
│                  OpenRouter API                              │
│   Modèles : Qwen · Llama · text-embedding-3-small           │
└──────────────────────────────────────────────────────────────┘
            │
┌───────────▼──────────────────────────────────────────────────┐
│          Infrastructure Docker (Mac mini M4)                 │
│     Qdrant (port 6333) · PostgreSQL (port 5432)             │
│     n8n (port 5678)                                         │
└──────────────────────────────────────────────────────────────┘
```

---

## Stack technique

| Composant | Technologie |
|---|---|
| Orchestration agents | Pydantic AI |
| LLMs + Embeddings | OpenRouter (une seule clé) |
| Intégrations | MCP (serveurs custom) |
| Mémoire vectorielle | Qdrant (Docker) |
| Sessions persistantes | PostgreSQL + asyncpg |
| Observabilité | Langfuse (traces + scores) |
| API interne | FastAPI + uvicorn |
| Frontend | React 18 + Vite + TypeScript + Tailwind |
| Automatisation | n8n (Docker) |
| Infra | Docker Compose, Git, GitHub Actions |

---

## Commandes

```bash
# Setup & déploiement
make setup              # venv + deps + pre-commit (première fois)
make docker-up          # démarrer Qdrant + PostgreSQL + n8n
make docker-down        # arrêter les containers
make start              # démarre tout l'environnement
make stop               # arrêt propre
make healthcheck        # vérifie Qdrant, PostgreSQL, API, n8n
make install-service    # installe le service launchd (démarrage au boot)

# Agents (terminal)
make dev-senior         # Agent Dev Senior
make biz-manager        # Agent Business Manager

# Frontend React
make frontend-install   # npm install (une seule fois)
make frontend           # Vite dev server sur http://localhost:5173
make frontend-build     # build de production

# API
make api                # démarrer l'API HTTP (port 8080)
make n8n                # ouvrir n8n dans le navigateur

# Mémoire
make index-codebase     # indexer le projet dans Qdrant
make index-codebase-force  # réindexer intégralement

# Qualité
make check              # lint + types + tests
make test               # tests uniquement
make lint               # ruff
make format             # ruff format
make typecheck          # mypy

# Observabilité
make eval-quality       # évaluation qualité (LLM-as-judge)
make eval-drift         # détection de dérive comportementale
make logs               # logs de l'API en temps réel
```

---

## Sécurité

### Configuration obligatoire en production

1. **OpenRouter** : définir `OPENROUTER_API_KEY` dans `.env`
2. **Clé API agents** : définir `AGENTS_API_KEY` — tous les endpoints requièrent le header `X-API-Key`
3. **n8n** : changer `N8N_PASSWORD` (jamais laisser `changeme`)
4. **PostgreSQL** : changer `POSTGRES_PASSWORD`
5. **Google credentials** : `credentials.json` et `token.json` sont dans `.gitignore` — ne jamais les committer
6. **Swagger** : désactiver en prod avec `DOCS_ENABLED=false`
7. **Frontend** : `VITE_API_KEY` dans `frontend/.env.local` pour passer la clé API au frontend en prod

### Générer une clé API sécurisée

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Installation

### Prérequis

- Mac mini M4 (ou tout Mac Apple Silicon)
- Python 3.11+
- Node.js 20+
- Docker Desktop
- Git

### Setup complet

```bash
git clone <repo-url> && cd Dev-Senior
cp .env.example .env
# → Éditer .env : OPENROUTER_API_KEY, POSTGRES_PASSWORD, AGENTS_API_KEY

make setup              # installe Python deps
make docker-up          # démarre Qdrant + PostgreSQL + n8n
make healthcheck        # vérifie que tout est OK
make frontend-install   # installe les deps npm (Node 20+ requis)
```

### Démarrage au boot (Mac mini M4)

```bash
make install-service   # installe le service launchd
# L'API redémarre automatiquement au reboot
```

---

## CI/CD

- **CI** (`.github/workflows/ci.yml`) : lint + types + tests + scan secrets — déclenché sur chaque push/PR
- **Deploy** (`.github/workflows/deploy.yml`) : déploiement automatique sur self-hosted runner (Mac mini M4) après merge sur `main`

---

## Structure du projet

```
Dev-Senior/
├── agents/                 ← Agents Pydantic AI
│   ├── dev_senior/         ← Agent technique
│   ├── biz_manager/        ← Agent business
│   └── config.py           ← OpenRouter model factory
├── mcp_servers/            ← Intégrations MCP custom
│   ├── github/             ← GitHub API
│   ├── google_workspace/   ← Drive, Gmail, Calendar
│   ├── crm/                ← HubSpot (adaptable)
│   └── seo/                ← Search Console + DataForSEO
├── api/                    ← API FastAPI
│   ├── auth.py             ← Authentification X-API-Key
│   ├── db.py               ← Pool asyncpg + get_pool()
│   ├── main.py             ← App + CORS + lifespan
│   ├── sessions.py         ← Sessions PostgreSQL
│   └── routes/             ← Endpoints par agent
├── memory/                 ← Mémoire vectorielle (Qdrant)
│   ├── dev_senior/         ← Indexer + retriever codebase
│   ├── biz_manager/        ← Contexte business
│   ├── embeddings.py       ← OpenRouter text-embedding-3-small
│   └── store.py            ← Client Qdrant
├── observability/          ← Tracing et évaluations
│   ├── langfuse_config.py  ← Configuration Langfuse (tracing + scores)
│   └── evals/              ← Eval qualité + détection dérive
├── frontend/               ← React + Vite + TypeScript + Tailwind
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api/agents.ts
│   │   ├── hooks/useChat.ts
│   │   └── components/
│   └── package.json
├── workflows/n8n/          ← 5 workflows JSON prêts à importer
├── infra/
│   ├── docker/             ← docker-compose (Qdrant + PostgreSQL + n8n)
│   └── deploy/             ← start/stop/healthcheck/launchd + init.sql
├── tests/                  ← Tests unitaires et intégration
├── docs/                   ← Guides utilisateurs
├── .github/workflows/      ← CI/CD GitHub Actions
├── CLAUDE.md               ← Instructions pour Claude Code
├── Makefile                ← Toutes les commandes
└── pyproject.toml          ← Dépendances et config
```

---

## Guides utilisateurs

- **Équipe technique** → [`docs/guide_dev_senior.md`](docs/guide_dev_senior.md)
- **Business managers / stagiaires** → [`docs/guide_biz_manager.md`](docs/guide_biz_manager.md)
- **Workflows n8n** → [`workflows/n8n/README.md`](workflows/n8n/README.md)

---

## Contribuer

1. Créer une branche depuis `main`
2. Développer et tester localement (`make check`)
3. Le pre-commit vérifie automatiquement le code et bloque les secrets
4. Ouvrir une PR — la CI tourne automatiquement
5. Merge → déploiement automatique sur le Mac mini M4
