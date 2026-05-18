# TODO — Feuille de route

Dernière mise à jour : 2026-05-18

---

## Phase 1 — Infrastructure & PoC ✅

- [x] `pyproject.toml` avec toutes les dépendances
- [x] `.env.example` complet
- [x] Agent Dev Senior (Pydantic AI)
- [x] Agent Business Manager (Pydantic AI)
- [x] Tests de smoke via `TestModel` (sans appel réseau)
- [x] Makefile complet

---

## Phase 2 — MCP Servers ✅

- [x] `mcp_servers/github/server.py` — list_prs, get_pr_diff, read_file, search_code, list_issues, create_issue, recent_commits
- [x] `mcp_servers/google_workspace/server.py` — Drive, Gmail, Calendar
- [x] `mcp_servers/crm/server.py` — HubSpot (contacts, deals, notes)
- [x] `mcp_servers/seo/server.py` — Search Console + DataForSEO
- [x] Agents câblés via `MCPServerStdio`
- [x] Tests mock pour GitHub server

---

## Phase 3 — Mémoire & Observabilité ✅

- [x] `memory/embeddings.py` — OpenRouter text-embedding-3-small (dim=1536)
- [x] `memory/store.py` — client Qdrant partagé
- [x] `memory/dev_senior/indexer.py` — indexation codebase CLI (incrémentale, Qdrant upsert)
- [x] `memory/dev_senior/retriever.py` — RAG (score_threshold=0.70, injection dans le prompt)
- [x] `memory/biz_manager/context.py` — mémoire contextuelle (notes, interactions, Qdrant)
- [x] `observability/langfuse_config.py` — Langfuse : traces par appel, no-op si clés absentes
- [x] `observability/evals/eval_quality.py` — LLM-as-judge (OpenRouter) + scores Langfuse
- [x] `observability/evals/eval_drift.py` — détection de dérive vs baseline

---

## Phase 4 — API & Workflows n8n ✅

- [x] `api/auth.py` — authentification X-API-Key (open en dev si clé absente)
- [x] `api/db.py` — pool asyncpg + `get_pool()` dépendance FastAPI
- [x] `api/main.py` — FastAPI + CORS (ports 5173, 5678) + lifespan (MCP + PostgreSQL + Langfuse)
- [x] `api/sessions.py` — sessions PostgreSQL avec TTL 60 min
- [x] `api/routes/dev_senior.py` — POST /chat, /reset, /health + trace Langfuse
- [x] `api/routes/biz_manager.py` — POST /chat, /task, /reset, /health + trace Langfuse
- [x] `infra/docker/docker-compose.yml` — Qdrant + PostgreSQL + n8n
- [x] `infra/deploy/init.sql` — schéma table sessions
- [x] 5 workflows n8n (PR Review, SEO Report, Email Triage, Lead Onboarding, Contenu)
- [x] Tous les workflows incluent le header `X-API-Key`

---

## Phase 5 — Frontend React ✅

- [x] `frontend/` — React 18 + Vite + TypeScript + Tailwind CSS
- [x] `frontend/src/App.tsx` — layout Sidebar + ChatWindow + InputBar
- [x] `frontend/src/api/agents.ts` — fetch API (sendChat, resetSession) + VITE_API_KEY
- [x] `frontend/src/hooks/useChat.ts` — state messages + session_id + reset
- [x] `frontend/src/components/Sidebar.tsx` — sélecteur agent (Dev Senior vert / Biz Manager bleu)
- [x] `frontend/src/components/ChatWindow.tsx` — liste messages + loading dots + erreurs
- [x] `frontend/src/components/MessageBubble.tsx` — bulles utilisateur / agent
- [x] `frontend/src/components/InputBar.tsx` — textarea + envoi Entrée + reset session
- [x] Vite proxy `/dev-senior` + `/biz-manager` → `http://localhost:8080`

---

## Phase 6 — Migration OpenRouter + Qdrant + PostgreSQL ✅

- [x] `agents/config.py` — OpenRouter via `OpenAIModel` (remplace Ollama + Claude API directe)
- [x] `memory/store.py` — client Qdrant (remplace ChromaDB)
- [x] `memory/embeddings.py` — OpenRouter text-embedding-3-small (remplace nomic-embed-text Ollama)
- [x] `api/sessions.py` — PostgreSQL asyncpg (remplace dict in-memory)
- [x] `pyproject.toml` — `qdrant-client` + `asyncpg` + `langfuse` (suppression `chromadb`, `logfire`)
- [x] `.env.example` — OPENROUTER_API_KEY, QDRANT_*, DATABASE_URL, POSTGRES_*, LANGFUSE_*
- [x] `infra/deploy/start.sh` — attend Qdrant + PostgreSQL (remplace Ollama + ChromaDB)
- [x] `infra/deploy/healthcheck.sh` — vérifie Qdrant + PostgreSQL
- [x] `infra/docker/pull-models.sh` — marqué obsolète (OpenRouter remplace Ollama)

---

## Phase 7 — Déploiement & CI/CD ✅

- [x] `docs/guide_dev_senior.md` — guide équipe technique (OpenRouter, Langfuse, frontend)
- [x] `docs/guide_biz_manager.md` — guide non-tech (interface web port 5173)
- [x] `.github/workflows/ci.yml` — lint + types + tests + TruffleHog (env vars mis à jour)
- [x] `.github/workflows/deploy.yml` — deploy sur self-hosted runner Mac mini M4
- [x] `infra/deploy/start.sh` / `stop.sh` / `healthcheck.sh`
- [x] `infra/deploy/com.agents.api.plist` + `install_launchd.sh` — service au boot
- [x] `CLAUDE.md`, `README.md`, `TODO.md` — documentation à jour

---

## Reste à faire (post-lancement)

- [ ] Installer le runner GitHub Actions sur le Mac mini M4
- [ ] `make install-service` sur la machine cible
- [ ] Remplir `.env` avec les vraies clés : `OPENROUTER_API_KEY`, `POSTGRES_PASSWORD`, `AGENTS_API_KEY`, `LANGFUSE_*`
- [ ] `make docker-up` → `make api` → `make frontend` : vérifier l'UI sur http://localhost:5173
- [ ] `make index-codebase` — indexer la codebase dans Qdrant
- [ ] Définir la baseline qualité : `make eval-set-baseline`
- [ ] Sessions de formation équipe technique (Agent Dev Senior)
- [ ] Sessions de formation business managers / stagiaires (interface web)
- [ ] Activer les 5 workflows n8n après configuration des credentials
- [ ] Recueil des premiers retours utilisateurs (J+15)

---

## Backlog v1.1

- [x] Tests d'intégration MCP (avec services réels mockés)
- [x] Mémoire multi-agent : Dev Senior et Biz Manager partagent certains contextes
- [ ] Sessions Redis pour l'API (si scale nécessaire)
- [x] Build frontend statique servi par FastAPI (`/app` — supprime le besoin de Vite en prod)
- [ ] Intégration Slack/Teams pour accéder aux agents depuis le chat
- [x] Évaluation automatique continue (cron quotidien)
- [ ] Dashboard métriques (latence P50/P95, taux d'erreur, qualité)
- [ ] Support `VITE_API_KEY` via `frontend/.env.local` pour la prod frontend
