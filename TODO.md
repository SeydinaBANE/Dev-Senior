# TODO — Feuille de route

Dernière mise à jour : 2026-05-18

---

## Phase 1 — Infrastructure & PoC ✅

- [x] `pyproject.toml` avec toutes les dépendances
- [x] `.env.example` complet
- [x] `infra/docker/docker-compose.yml` — Ollama + ChromaDB + n8n
- [x] `infra/docker/pull-models.sh` — qwen2.5-coder, llama3.1, nomic-embed-text
- [x] Agent Dev Senior (Pydantic AI + Ollama, switch cloud)
- [x] Agent Business Manager (Pydantic AI + Ollama, switch cloud)
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

- [x] `memory/embeddings.py` — embed + chunk via Ollama nomic-embed-text
- [x] `memory/store.py` — client ChromaDB partagé
- [x] `memory/dev_senior/indexer.py` — indexation codebase CLI (incrémentale)
- [x] `memory/dev_senior/retriever.py` — RAG (contexte injecté avant chaque requête)
- [x] `memory/biz_manager/context.py` — mémoire contextuelle (notes, interactions)
- [x] `observability/logfire_config.py` — Logfire + instrumentation Pydantic AI/httpx
- [x] `observability/evals/eval_quality.py` — LLM-as-judge (Claude Haiku)
- [x] `observability/evals/eval_drift.py` — détection de dérive vs baseline

---

## Phase 4 — API & Workflows n8n ✅

- [x] `api/auth.py` — authentification X-API-Key
- [x] `api/main.py` — FastAPI + CORS + lifespan (MCP servers persistants)
- [x] `api/sessions.py` — sessions avec TTL 60 min
- [x] `api/routes/dev_senior.py` — POST /chat, /reset, /health
- [x] `api/routes/biz_manager.py` — POST /chat, /task (one-shot), /reset, /health
- [x] `infra/docker/docker-compose.yml` — n8n ajouté
- [x] 5 workflows n8n (PR Review, SEO Report, Email Triage, Lead Onboarding, Contenu)
- [x] Tous les workflows incluent le header `X-API-Key`

---

## Phase 5 — Déploiement & Formation ✅

- [x] `docs/guide_dev_senior.md` — guide équipe technique
- [x] `docs/guide_biz_manager.md` — guide non-tech (exemples, workflows n8n)
- [x] `.github/workflows/ci.yml` — lint + types + tests + TruffleHog
- [x] `.github/workflows/deploy.yml` — deploy sur self-hosted runner Mac mini M4
- [x] `infra/deploy/start.sh` / `stop.sh` / `healthcheck.sh`
- [x] `infra/deploy/com.agents.api.plist` + `install_launchd.sh` — service au boot

---

## Cohérence & Sécurité ✅

- [x] `pyproject.toml` — suppression du doublon `chromadb`, nettoyage `logfire` extras
- [x] `.env.example` — suppression des doublons, `AGENTS_API_KEY` ajouté, avertissements sécurité
- [x] `.gitignore` — patterns de secrets renforcés (`service_account.json`, `*.p12`, etc.)
- [x] API protégée par `X-API-Key` sur tous les endpoints (sauf `/health`)
- [x] CORS restreint aux origines configurées
- [x] Swagger désactivable via `DOCS_ENABLED=false`
- [x] Workflows n8n mis à jour avec `X-API-Key`
- [x] `README.md`, `CLAUDE.md`, `TODO.md` mis à jour

---

## Reste à faire (post-lancement)

- [ ] Installer le runner GitHub Actions sur le Mac mini M4
- [ ] Lancer `make install-service` sur la machine cible
- [ ] Remplir `.env` avec les vraies clés API
- [ ] Télécharger `credentials.json` depuis Google Cloud Console
- [ ] Lancer `make models` et vérifier les modèles
- [ ] `make index-codebase` sur la codebase principale
- [ ] Définir la baseline qualité : `make eval-set-baseline`
- [ ] Sessions de formation équipe tech (Agent Dev Senior)
- [ ] Sessions de formation business managers / stagiaires
- [ ] Activer les 5 workflows n8n après configuration des credentials
- [ ] Recueil des premiers retours utilisateurs (J+15)

---

## Backlog v1.1

- [ ] Tests d'intégration MCP (avec services réels mockés)
- [ ] Interface web légère pour les non-tech (au lieu du terminal)
- [ ] Mémoire multi-agent : Dev Senior et Biz Manager partagent certains contextes
- [ ] Support MLX natif Apple Silicon (si perf Docker insuffisante)
- [ ] Sessions Redis pour l'API (si scale nécessaire)
- [ ] Intégration Slack/Teams pour accéder aux agents depuis le chat
- [ ] Évaluation automatique continue (cron quotidien)
- [ ] Dashboard métriques (latence P50/P95, taux d'erreur, qualité)
