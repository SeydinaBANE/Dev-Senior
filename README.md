# Agents IA Internes — Dev Senior & Business Manager

Deux agents IA déployés en interne sur Mac mini M4 pour augmenter la productivité de l'équipe technique et des business managers.

---

## Démarrage rapide

```bash
# 1. Setup (une seule fois)
cp .env.example .env        # remplir les clés
make setup                  # venv + deps + pre-commit

# 2. Démarrer tout l'environnement
make start                  # Docker (Ollama + ChromaDB + n8n) + API agents

# 3. Vérifier que tout tourne
make healthcheck

# 4. Utiliser les agents
make dev-senior             # terminal — agent technique
make biz-manager            # terminal — agent business
# ou ouvrir http://localhost:5678 pour les workflows n8n
```

---

## Les deux agents

### Agent Dev Senior
**Utilisateurs :** équipe technique  
**Capacités :** développement complexe, architecture, debugging, code reviews, refactoring, documentation  
**Modèle :** `qwen2.5-coder:7b` via Ollama (local) · `claude-sonnet-4-6` (cloud)  
**Mémoire :** RAG sur la codebase indexée dans ChromaDB

### Agent Business Manager
**Utilisateurs :** business managers, stagiaires  
**Capacités :** marketing digital, SEO, réseaux sociaux, contenu, emails, CRM, automatisation  
**Modèle :** `llama3.1:8b` via Ollama (local) · `claude-sonnet-4-6` (cloud)  
**Mémoire :** historique des interactions mémorisé automatiquement

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Agents (Pydantic AI)                      │
│  ┌────────────────────┐       ┌───────────────────────┐     │
│  │    Dev Senior      │       │   Business Manager    │     │
│  │  qwen2.5-coder:7b  │       │    llama3.1:8b        │     │
│  └────────┬───────────┘       └──────────┬────────────┘     │
└───────────┼──────────────────────────────┼──────────────────┘
            │             MCP              │
┌───────────▼──────────────────────────────▼──────────────────┐
│                    MCP Servers (custom)                      │
│       GitHub    Google Workspace    CRM (HubSpot)    SEO    │
└──────────────────────────────────────────────────────────────┘
            │
┌───────────▼──────────────────────────────────────────────────┐
│          FastAPI (port 8080) — API interne sécurisée         │
│              Auth : X-API-Key · CORS : localhost             │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                  n8n (port 5678)                             │
│   PR Review · SEO Report · Email Triage · Lead · Contenu    │
└──────────────────────────────────────────────────────────────┘
            │
┌───────────▼──────────────────────────────────────────────────┐
│          Inférence locale — Mac mini M4 (Docker)            │
│     Ollama (port 11434) · ChromaDB (port 8000)              │
│     Modèles : qwen2.5-coder · llama3.1 · nomic-embed-text   │
└──────────────────────────────────────────────────────────────┘
```

---

## Stack technique

| Composant | Technologie |
|---|---|
| Orchestration agents | Pydantic AI |
| LLMs cloud | Claude API (Anthropic) |
| LLMs locaux | Ollama via Docker |
| Intégrations | MCP (serveurs custom) |
| Mémoire vectorielle | ChromaDB (Docker) |
| Embeddings | nomic-embed-text (Ollama) |
| Observabilité | Logfire |
| API interne | FastAPI + uvicorn |
| Automatisation | n8n (Docker) |
| Infra | Docker Compose, Git, GitHub Actions |

---

## Commandes

```bash
# Setup & déploiement
make setup              # venv + deps + pre-commit (première fois)
make start              # démarre tout l'environnement
make stop               # arrêt propre
make healthcheck        # vérifie Ollama, ChromaDB, API, n8n
make install-service    # installe le service launchd (démarrage au boot)

# Agents (terminal)
make dev-senior         # Agent Dev Senior (Ollama local)
make dev-senior-cloud   # Agent Dev Senior (Claude API)
make biz-manager        # Agent Business Manager (Ollama local)
make biz-manager-cloud  # Agent Business Manager (Claude API)

# Docker
make docker-up          # démarrer les containers
make docker-down        # arrêter les containers
make models             # télécharger les modèles LLM

# API & n8n
make api                # démarrer l'API HTTP (port 8080)
make n8n                # ouvrir n8n dans le navigateur

# Mémoire
make index-codebase     # indexer le projet dans ChromaDB
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

1. **Clé API** : définir `AGENTS_API_KEY` dans `.env` — tous les endpoints API requièrent le header `X-API-Key`
2. **n8n** : changer `N8N_PASSWORD` (jamais laisser `changeme`)
3. **ChromaDB** : changer `CHROMA_TOKEN` (jamais laisser `dev-token`)
4. **Google credentials** : `credentials.json` et `token.json` sont dans `.gitignore` — ne jamais les committer
5. **Swagger** : désactiver en prod avec `DOCS_ENABLED=false`

### Ce qui est protégé

- Tous les endpoints API (sauf `/health`) requièrent `X-API-Key`
- CORS restreint aux origines configurées dans `CORS_ORIGINS`
- Pre-commit bloque le commit de secrets (`detect-private-key`, `.env`)
- GitHub Actions scanne les secrets avec TruffleHog

### Générer une clé API sécurisée

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Installation

### Prérequis

- Mac mini M4 (ou tout Mac Apple Silicon)
- Python 3.11+
- Docker Desktop
- Git

### Setup complet

```bash
git clone <repo-url> && cd Dev-Senior
cp .env.example .env
# → Éditer .env avec vos clés API

make setup       # installe tout
make docker-up   # démarre les services
make models      # télécharge les modèles (~5 min)
make healthcheck # vérifie que tout est OK
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

Pour activer le déploiement automatique : installer le runner GitHub Actions sur le Mac mini (`Settings → Actions → Runners → New self-hosted runner`).

---

## Structure du projet

```
Dev-Senior/
├── agents/                 ← Agents Pydantic AI
│   ├── dev_senior/         ← Agent technique
│   ├── biz_manager/        ← Agent business
│   └── config.py           ← Switch local/cloud
├── mcp_servers/            ← Intégrations MCP custom
│   ├── github/             ← GitHub API
│   ├── google_workspace/   ← Drive, Gmail, Calendar
│   ├── crm/                ← HubSpot (adaptable)
│   └── seo/                ← Search Console + DataForSEO
├── api/                    ← API FastAPI (pour n8n)
│   ├── auth.py             ← Authentification X-API-Key
│   ├── main.py             ← App + CORS + lifespan
│   └── routes/             ← Endpoints par agent
├── memory/                 ← Mémoire vectorielle
│   ├── dev_senior/         ← Indexer + retriever codebase
│   ├── biz_manager/        ← Contexte business
│   ├── embeddings.py       ← Ollama nomic-embed-text
│   └── store.py            ← Client ChromaDB
├── observability/          ← Tracing et évaluations
│   ├── logfire_config.py   ← Configuration Logfire
│   └── evals/              ← Eval qualité + détection dérive
├── workflows/n8n/          ← 5 workflows JSON prêts à importer
├── infra/
│   ├── docker/             ← docker-compose (Ollama+ChromaDB+n8n)
│   └── deploy/             ← Scripts start/stop/healthcheck/launchd
├── tests/                  ← Tests unitaires et intégration
├── docs/                   ← Guides utilisateurs
│   ├── guide_dev_senior.md
│   └── guide_biz_manager.md
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
