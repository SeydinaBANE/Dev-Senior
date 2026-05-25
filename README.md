# Agents IA Internes — Dev Senior & Business Manager

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Pydantic AI](https://img.shields.io/badge/Pydantic_AI-latest-E92063?style=flat-square&logo=pydantic&logoColor=white)](https://ai.pydantic.dev)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-API-6366F1?style=flat-square&logo=openai&logoColor=white)](https://openrouter.ai)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Qdrant](https://img.shields.io/badge/Qdrant-vector_DB-DC382D?style=flat-square&logo=qdrant&logoColor=white)](https://qdrant.tech)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io)
[![Langfuse](https://img.shields.io/badge/Langfuse-observabilité-000000?style=flat-square&logo=langfuse&logoColor=white)](https://langfuse.com)
[![n8n](https://img.shields.io/badge/n8n-workflows-EA4B71?style=flat-square&logo=n8n&logoColor=white)](https://n8n.io)
[![Slack](https://img.shields.io/badge/Slack-integration-4A154B?style=flat-square&logo=slack&logoColor=white)](https://api.slack.com)
[![Teams](https://img.shields.io/badge/Teams-integration-6264A7?style=flat-square&logo=microsoftteams&logoColor=white)](https://learn.microsoft.com/fr-fr/microsoftteams/platform/)
[![CI](https://img.shields.io/github/actions/workflow/status/SeydinaBANE/Dev-Senior/ci.yml?branch=main&style=flat-square&label=CI&logo=github)](https://github.com/SeydinaBANE/Dev-Senior/actions)
[![License](https://img.shields.io/badge/licence-MIT-22C55E?style=flat-square)](LICENSE)

Deux agents IA déployés en interne sur Mac mini M4 pour augmenter la productivité de l'équipe technique et des business managers.

---

## Démarrage rapide

```bash
# 1. Setup (une seule fois)
cp .env.example .env                # remplir OPENROUTER_API_KEY + POSTGRES_PASSWORD
make setup                          # venv + deps + pre-commit

# 2. Démarrer tout l'environnement
make docker-up                      # Qdrant + PostgreSQL + Redis + n8n
make api                            # FastAPI port 8080

# 3. Ouvrir le frontend
make frontend-install               # npm install (une seule fois)
make frontend-env                   # créer frontend/.env.local (remplir VITE_API_KEY)
make frontend                       # Vite dev server → http://localhost:5173

# 4. Vérifier que tout tourne
make healthcheck
```

---

## Les deux agents

### Agent Dev Senior
**Utilisateurs :** équipe technique
**Capacités :** développement complexe, architecture, debugging, code reviews, refactoring, documentation
**Modèle :** `qwen/qwen-2.5-coder-7b-instruct` via OpenRouter
**Mémoire :** RAG sur la codebase indexée dans Qdrant + contexte partagé avec le Biz Manager

### Agent Business Manager
**Utilisateurs :** business managers, stagiaires
**Capacités :** marketing digital, SEO, réseaux sociaux, contenu, emails, CRM, automatisation
**Modèle :** `meta-llama/llama-3.1-8b-instruct` via OpenRouter
**Mémoire :** historique des interactions mémorisé automatiquement dans Qdrant + contexte partagé avec Dev Senior

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  Clients                                                         │
│  React /app  ·  Vite :5173  ·  Slack /dev-senior  ·  Teams      │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼───────────────────────────────────────┐
│  FastAPI :8080                                                   │
│  /dev-senior  /biz-manager  /slack  /teams  /metrics  /app      │
│  Auth : X-API-Key · CORS · Slack HMAC · Teams HMAC              │
└──────┬──────────────────────────────────────────────────────┬────┘
       │ Pydantic AI                                          │ Sessions
┌──────▼────────────────────────────────────────────────┐  ┌─▼──────────┐
│  Agents                                               │  │  Redis     │
│  Dev Senior (Qwen 7B)  ·  Business Manager (Llama 8B) │  │  (opt.)    │
└──────┬────────────────────────────────────────────────┘  └─┬──────────┘
       │ MCP                                                  │ fallback
┌──────▼────────────────────────────────────────────────┐  ┌─▼──────────┐
│  MCP Servers                                          │  │ PostgreSQL │
│  GitHub · Google Workspace · CRM HubSpot · SEO       │  └────────────┘
└──────┬────────────────────────────────────────────────┘
       │ embeddings + LLMs
┌──────▼────────────────────────────────────────────────┐
│  OpenRouter API                                       │
│  Qwen · Llama · text-embedding-3-small               │
└──────┬────────────────────────────────────────────────┘
       │
┌──────▼────────────────────────────────────────────────┐
│  Qdrant (mémoire vectorielle)                         │
│  collections : codebase · biz_context · shared       │
└───────────────────────────────────────────────────────┘
```

---

## Stack technique

| Composant | Technologie |
|---|---|
| Orchestration agents | Pydantic AI |
| LLMs + Embeddings | OpenRouter (une seule clé) |
| Intégrations | MCP custom (GitHub, Google, HubSpot, SEO) |
| Mémoire vectorielle | Qdrant — 3 collections : `codebase`, `biz_context`, `shared` |
| Sessions | Redis (TTL natif) ou PostgreSQL + asyncpg (fallback automatique) |
| Observabilité | Langfuse (traces + LLM-as-judge + dérive) |
| Dashboard métriques | FastAPI `/metrics` + composant React (P50/P95, taux d'erreur, qualité) |
| API interne | FastAPI + uvicorn — réponses complètes (`/chat`), streaming SSE (`/chat/stream`), upload de fichiers (`/upload`) |
| Frontend | React 18 + Vite + TypeScript + Tailwind — streaming token-par-token, upload de fichiers, servi en prod via FastAPI `/app` ou Vercel |
| Extraction de fichiers | `pypdf` (PDF) + `python-docx` (DOCX) + texte/code natif — 20 000 chars max |
| Chat d'équipe | Slack slash commands · Teams outgoing webhook |
| Automatisation | n8n — 5 workflows prêts à l'emploi |
| Infra | Docker Compose, GitHub Actions CI/CD, launchd (macOS) |

---

## Fonctionnalités

### Mémoire partagée entre agents
Les deux agents partagent une collection Qdrant `shared`. Les interactions Biz Manager pertinentes sont automatiquement accessibles à Dev Senior, et vice versa. Cela permet, par exemple, que Dev Senior soit au courant d'une décision métier prise avec le Biz Manager.

### Sessions Redis / PostgreSQL
Le backend de sessions se sélectionne automatiquement selon `REDIS_URL` :
- **Redis** (recommandé en prod) : TTL natif, O(1), aucune maintenance
- **PostgreSQL** (défaut) : sessions persistantes avec TTL 60 min, pool asyncpg

Les sessions sont partagées entre tous les points d'entrée — frontend, Slack et Teams utilisent le même store avec des clés distinctes (`slack:{channel_id}:{user_id}`, `teams:{conversation_id}`).

### Dashboard métriques
Accessible via le frontend (onglet Dashboard) ou directement :
```bash
curl http://localhost:8080/metrics -H "X-API-Key: <votre-clé>"
```
Affiche latence P50/P95, taux d'erreur et scores de qualité LLM-as-judge pour chaque agent.

### Intégration Slack
Créer une Slack App avec deux slash commands :

| Commande | Endpoint | Agent |
|---|---|---|
| `/dev-senior <message>` | `POST /slack/command` | Dev Senior |
| `/biz-manager <message>` | `POST /slack/command` | Business Manager |

Slack reçoit un accusé immédiat ; la réponse de l'agent est postée en différé via `response_url`.

**Mémoire par canal :** chaque utilisateur conserve un fil de conversation persistant par canal Slack (clé `slack:{channel_id}:{user_id}`). Envoyer `/dev-senior reset` efface la mémoire.

### Intégration Teams
Créer un outgoing webhook Teams pointant vers `POST /teams/message`.
Routage par mention : `@dev-senior <message>` ou `@biz-manager <message>`.

**Mémoire par conversation :** l'historique est conservé par conversation Teams (clé `teams:{conversation_id}`). Envoyer `reset` dans la conversation réinitialise la mémoire.

### Streaming des réponses (SSE)
Le frontend affiche les tokens au fur et à mesure via Server-Sent Events :

```
Envoi → [dots pensée] → premier token → [texte qui s'écrit avec curseur |] → complet
```

Deux modes coexistent sur l'API :
| Endpoint | Mode | Usage |
|---|---|---|
| `POST /dev-senior/chat` | Réponse complète (JSON) | n8n, intégrations tierces |
| `POST /dev-senior/chat/stream` | SSE token-par-token | Frontend, Slack (background) |

### Upload de fichiers
Joindre un fichier à n'importe quel message via le bouton 📎 dans le frontend.

- **Formats supportés** : texte/code (`.py`, `.ts`, `.md`, `.json`, `.csv`, `.yaml`…), `.pdf`, `.docx`
- **Taille max extraite** : 20 000 caractères (tronqué avec notice si dépassé)
- **Fonctionnement** : le serveur extrait le texte via `POST /{agent}/upload`, le renvoie au client. Lors de l'envoi du message, le texte est inclus dans `document_context` → injecté dans le prompt sous la section `[Document joint]`. Aucun stockage serveur.

```http
POST /dev-senior/upload          → { filename, text, size_chars }
POST /dev-senior/chat            ← { message, session_id, document_context? }
```

### Évaluation automatique quotidienne
Un job launchd (`make install-eval-cron`) tourne chaque nuit à 2h :
- Évalue 10 interactions par agent (LLM-as-judge via OpenRouter)
- Pousse les scores dans Langfuse
- Détecte les dérives comportementales vs baseline

---

## Commandes

```bash
# Setup & déploiement
make setup              # venv + deps + pre-commit (première fois)
make docker-up          # démarrer Qdrant + PostgreSQL + Redis + n8n
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
make frontend-env       # crée frontend/.env.local depuis le template
make frontend           # Vite dev server → http://localhost:5173
make frontend-build     # build de production (bakes VITE_API_KEY)
make serve-prod         # build frontend + démarre l'API (port 8080)

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
make eval-set-baseline  # fixer la baseline qualité
make install-eval-cron  # installer le cron d'évaluation quotidienne
make logs               # logs de l'API en temps réel
```

---

## Sécurité

### Configuration obligatoire en production

| Variable | Description |
|---|---|
| `OPENROUTER_API_KEY` | Clé OpenRouter — LLMs + embeddings |
| `AGENTS_API_KEY` | Auth interne — tous les endpoints requièrent `X-API-Key` |
| `POSTGRES_PASSWORD` | Mot de passe PostgreSQL — ne jamais laisser la valeur d'exemple |
| `SLACK_SIGNING_SECRET` | Vérification HMAC-SHA256 des slash commands Slack |
| `TEAMS_WEBHOOK_KEY` | Vérification HMAC-SHA256 des webhooks Teams |
| `DOCS_ENABLED=false` | Désactiver Swagger UI en prod |

```bash
# Générer une clé API sécurisée
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Règles absolues
- Toutes les clés viennent de `os.getenv()` — jamais hardcodées
- `credentials.json`, `token.json`, `.env`, `frontend/.env.local` → gitignorés
- Le pre-commit bloque automatiquement les commits avec secrets détectés

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

# Backend
cp .env.example .env
# → Éditer .env : OPENROUTER_API_KEY, POSTGRES_PASSWORD, AGENTS_API_KEY
make setup
make docker-up
make healthcheck

# Frontend
make frontend-install
make frontend-env
# → Éditer frontend/.env.local : VITE_API_KEY = valeur de AGENTS_API_KEY
```

### Démarrage au boot (Mac mini M4)

```bash
make install-service        # installe le service launchd (API)
make install-eval-cron      # installe le cron d'évaluation quotidienne
```

### Production (frontend servi par FastAPI)

```bash
make frontend-build         # build → frontend/dist/
make serve-prod             # FastAPI sert /app + API sur :8080
# → Interface disponible sur http://localhost:8080/app
```

---

## CI/CD

- **CI** (`.github/workflows/ci.yml`) : lint + types + tests + scan secrets — déclenché sur chaque push/PR
- **Deploy** (`.github/workflows/deploy.yml`) : déploiement automatique sur self-hosted runner (Mac mini M4) après merge sur `main`

---

## Structure du projet

```
Dev-Senior/
├── agents/
│   ├── dev_senior/         ← agent.py, prompts.py, __main__.py
│   ├── biz_manager/        ← agent.py, prompts.py, __main__.py
│   └── config.py           ← OpenRouter model factory
├── mcp_servers/
│   ├── github/             ← list_prs, get_pr_diff, read_file, create_issue…
│   ├── google_workspace/   ← Drive, Gmail, Calendar
│   ├── crm/                ← HubSpot (contacts, deals, notes)
│   └── seo/                ← Search Console + DataForSEO
├── api/
│   ├── auth.py             ← X-API-Key (open en dev si clé absente)
│   ├── db.py               ← pool asyncpg + get_pool()
│   ├── main.py             ← App + CORS + lifespan (MCP + sessions)
│   ├── sessions.py         ← SessionStore abstrait (Redis ou PostgreSQL)
│   ├── metrics_store.py    ← métriques in-memory (P50/P95, erreurs)
│   ├── file_extractor.py   ← extraction texte (txt/code, PDF, DOCX) — 20k chars max
│   └── routes/
│       ├── dev_senior.py   ← POST /dev-senior/chat|stream|upload|reset|health
│       ├── biz_manager.py  ← POST /biz-manager/chat|stream|upload|task|reset|health
│       ├── metrics.py      ← GET /metrics (latence + qualité)
│       ├── slack.py        ← POST /slack/command (slash commands)
│       └── teams.py        ← POST /teams/message (outgoing webhook)
├── memory/
│   ├── embeddings.py       ← OpenRouter text-embedding-3-small
│   ├── store.py            ← client Qdrant partagé
│   ├── dev_senior/         ← indexer.py + retriever.py (RAG codebase)
│   ├── biz_manager/        ← context.py (mémoire interactions)
│   └── shared/             ← memory.py (contexte cross-agent, collection "shared")
├── observability/
│   ├── langfuse_config.py  ← traces + scores LLM-as-judge
│   └── evals/
│       ├── eval_quality.py ← LLM-as-judge via OpenRouter
│       ├── eval_drift.py   ← détection de dérive vs baseline
│       └── cron_eval.py    ← orchestrateur d'évaluation quotidienne
├── frontend/
│   ├── .env.example        ← template VITE_API_KEY + VITE_API_URL
│   ├── vercel.json         ← règle rewrite SPA pour Vercel
│   ├── src/
│   │   ├── App.tsx         ← layout Sidebar + vue active (chat ou dashboard)
│   │   ├── api/agents.ts   ← fetch API (VITE_API_KEY + VITE_API_URL + uploadFile)
│   │   ├── hooks/useChat.ts ← pendingDoc, attachFile, detachFile, uploading
│   │   └── components/
│   │       ├── Sidebar.tsx         ← sélecteur agent + nav dashboard
│   │       ├── ChatWindow.tsx
│   │       ├── MessageBubble.tsx   ← chip 📎 si fichier joint
│   │       ├── InputBar.tsx        ← bouton trombone + chip fichier
│   │       └── MetricsDashboard.tsx ← P50/P95, taux d'erreur, qualité
│   └── vite.config.ts      ← base pilotable via VITE_BASE_PATH (/app/ self-hosted, / Vercel)
├── workflows/n8n/          ← 5 workflows JSON (PR Review, SEO, Email, Lead, Contenu)
├── infra/
│   ├── docker/             ← docker-compose (Qdrant + PostgreSQL + Redis + n8n)
│   └── deploy/             ← start/stop/healthcheck + launchd (API + eval cron)
├── tests/
│   ├── agents/             ← test_smoke.py (TestModel, sans appel réseau)
│   ├── mcp_servers/        ← test_github.py, test_crm.py, test_seo.py, test_google_workspace.py
│   ├── memory/             ← test_shared.py
│   ├── observability/      ← test_evals.py
│   └── api/                ← test_sessions.py, test_slack.py, test_teams.py, test_upload.py
├── docs/
│   ├── guide_dev_senior.md
│   ├── guide_biz_manager.md
│   └── deploy_railway_vercel.md ← déploiement cloud Railway + Vercel
├── .github/workflows/      ← ci.yml + deploy.yml
├── railway.toml            ← config déploiement Railway (Nixpacks)
├── CLAUDE.md               ← instructions Claude Code
├── Makefile
└── pyproject.toml
```

---

## Guides utilisateurs

- **Équipe technique** → [`docs/guide_dev_senior.md`](docs/guide_dev_senior.md)
- **Business managers / stagiaires** → [`docs/guide_biz_manager.md`](docs/guide_biz_manager.md)
- **Déploiement Railway + Vercel** → [`docs/deploy_railway_vercel.md`](docs/deploy_railway_vercel.md)

---

## Contribuer

1. Créer une branche depuis `main`
2. Développer et tester localement (`make check`)
3. Le pre-commit vérifie automatiquement le code et bloque les secrets
4. Ouvrir une PR — la CI tourne automatiquement
5. Merge → déploiement automatique sur le Mac mini M4
