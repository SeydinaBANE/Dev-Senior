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

- [x] `memory/embeddings.py` — embed + chunk via OpenRouter text-embedding-3-small
- [x] `memory/store.py` — client Qdrant partagé
- [x] `memory/dev_senior/indexer.py` — indexation codebase CLI (incrémentale, Qdrant upsert)
- [x] `memory/dev_senior/retriever.py` — RAG (contexte injecté avant chaque requête)
- [x] `memory/biz_manager/context.py` — mémoire contextuelle (notes, interactions, Qdrant)
- [x] `observability/langfuse_config.py` — Langfuse : traces par appel agent, scores LLM-as-judge
- [x] `observability/evals/eval_quality.py` — LLM-as-judge (OpenRouter) + scores Langfuse
- [x] `observability/evals/eval_drift.py` — détection de dérive vs baseline

---

## Phase 4 — API & Workflows n8n ✅

- [x] `api/auth.py` — authentification X-API-Key
- [x] `api/db.py` — pool asyncpg + `get_pool()` dépendance FastAPI
- [x] `api/main.py` — FastAPI + CORS (port 5173 inclus) + lifespan (MCP + PostgreSQL)
- [x] `api/sessions.py` — sessions PostgreSQL avec TTL 60 min
- [x] `api/routes/dev_senior.py` — POST /chat, /reset, /health
- [x] `api/routes/biz_manager.py` — POST /chat, /task (one-shot), /reset, /health
- [x] `infra/docker/docker-compose.yml` — Qdrant + PostgreSQL + n8n
- [x] `infra/deploy/init.sql` — schéma table sessions
- [x] 5 workflows n8n (PR Review, SEO Report, Email Triage, Lead Onboarding, Contenu)
- [x] Tous les workflows incluent le header `X-API-Key`

---

## Phase 5 — Frontend React ✅

- [x] `frontend/` — React 18 + Vite + TypeScript + Tailwind CSS
- [x] `frontend/src/App.tsx` — layout Sidebar + ChatWindow + InputBar
- [x] `frontend/src/api/agents.ts` — fetch API (sendChat, resetSession)
- [x] `frontend/src/hooks/useChat.ts` — state messages + session_id + reset
- [x] `frontend/src/components/Sidebar.tsx` — sélecteur agent (Dev Senior / Biz Manager)
- [x] `frontend/src/components/ChatWindow.tsx` — liste messages + loading dots + erreurs
- [x] `frontend/src/components/MessageBubble.tsx` — bulles utilisateur / agent
- [x] `frontend/src/components/InputBar.tsx` — textarea + envoi + reset
- [x] Vite proxy `/dev-senior` + `/biz-manager` → `http://localhost:8080`

---

## Phase 6 — Migration & Cohérence ✅

- [x] `agents/config.py` — OpenRouter via `OpenAIModel` (remplace Ollama + Claude API)
- [x] `memory/store.py` — client Qdrant (remplace ChromaDB)
- [x] `memory/embeddings.py` — OpenRouter text-embedding-3-small (remplace nomic-embed-text)
- [x] `api/sessions.py` — PostgreSQL asyncpg (remplace dict in-memory)
- [x] `pyproject.toml` — `qdrant-client` + `asyncpg` (suppression `chromadb`)
- [x] `.env.example` — `OPENROUTER_API_KEY`, `QDRANT_*`, `DATABASE_URL`, `POSTGRES_*`
- [x] `infra/deploy/healthcheck.sh` — Qdrant + PostgreSQL (remplace Ollama + ChromaDB)
- [x] `Makefile` — `make frontend`, `make frontend-build`, `make frontend-install`
- [x] `CLAUDE.md`, `README.md`, `TODO.md` mis à jour

---

## Phase 7 — Déploiement ✅

- [x] `docs/guide_dev_senior.md` — guide équipe technique
- [x] `docs/guide_biz_manager.md` — guide non-tech (exemples, workflows n8n)
- [x] `.github/workflows/ci.yml` — lint + types + tests + TruffleHog
- [x] `.github/workflows/deploy.yml` — deploy sur self-hosted runner Mac mini M4
- [x] `infra/deploy/start.sh` / `stop.sh` / `healthcheck.sh`
- [x] `infra/deploy/com.agents.api.plist` + `install_launchd.sh` — service au boot

---

## Reste à faire (post-lancement)

- [ ] Installer le runner GitHub Actions sur le Mac mini M4
- [ ] Lancer `make install-service` sur la machine cible
- [ ] Remplir `.env` avec les vraies clés API (OPENROUTER_API_KEY, POSTGRES_PASSWORD, AGENTS_API_KEY)
- [ ] `make docker-up` puis `make api` pour vérifier le démarrage
- [ ] `make index-codebase` sur la codebase principale
- [ ] `make frontend-install && make frontend` — tester l'UI
- [ ] Définir la baseline qualité : `make eval-set-baseline`
- [ ] Sessions de formation équipe tech (Agent Dev Senior)
- [ ] Sessions de formation business managers / stagiaires
- [ ] Activer les 5 workflows n8n après configuration des credentials
- [ ] Recueil des premiers retours utilisateurs (J+15)

---

## Backlog v1.1

- [ ] Tests d'intégration MCP (avec services réels mockés)
- [ ] Mémoire multi-agent : Dev Senior et Biz Manager partagent certains contextes
- [ ] Sessions Redis pour l'API (si scale nécessaire)
- [ ] Intégration Slack/Teams pour accéder aux agents depuis le chat
- [ ] Évaluation automatique continue (cron quotidien)
- [ ] Dashboard métriques (latence P50/P95, taux d'erreur, qualité)
- [ ] Build frontend statique servi par FastAPI (`/app`)
