.DEFAULT_GOAL := help
SHELL := /bin/bash
PYTHON := python3
VENV := .venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
MYPY := $(VENV)/bin/mypy
RUFF := $(VENV)/bin/ruff

.PHONY: help setup install dev docker-up docker-down dev-senior biz-manager test lint typecheck format clean frontend frontend-build frontend-install frontend-env serve-prod install-eval-cron run-eval-cron

# ── Aide ─────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "  Dev Senior & Business Manager — Commandes disponibles"
	@echo ""
	@echo "  Setup"
	@echo "    make setup              Crée le venv et installe toutes les dépendances"
	@echo "    make install            Installe uniquement les dépendances (venv existant)"
	@echo ""
	@echo "  Docker"
	@echo "    make docker-up          Démarre Qdrant + PostgreSQL + n8n"
	@echo "    make docker-down        Arrête les containers"
	@echo ""
	@echo "  Agents"
	@echo "    make dev-senior         Lance l'agent Dev Senior (terminal)"
	@echo "    make biz-manager        Lance l'agent Business Manager (terminal)"
	@echo ""
	@echo "  Frontend React"
	@echo "    make frontend-install   Installe les dépendances npm"
	@echo "    make frontend-env       Crée frontend/.env.local depuis l'exemple"
	@echo "    make frontend           Lance le dev server Vite (port 5173)"
	@echo "    make frontend-build     Build de production"
	@echo ""
	@echo "  Qualité"
	@echo "    make test               Lance tous les tests"
	@echo "    make lint               Vérifie le style avec ruff"
	@echo "    make format             Formate le code avec ruff"
	@echo "    make typecheck          Vérifie les types avec mypy"
	@echo "    make check              lint + typecheck + test"
	@echo ""
	@echo "  API & n8n"
	@echo "    make api                Démarre l'API HTTP agents (port 8080)"
	@echo "    make serve-prod         Build frontend + démarre l'API (prod, port 8080)"
	@echo "    make n8n                Ouvre n8n dans le navigateur"
	@echo ""
	@echo "  Mémoire"
	@echo "    make index-codebase     Indexe le projet courant dans Qdrant"
	@echo "    make index-codebase-force   Réindexe intégralement"
	@echo ""
	@echo "  Observabilité"
	@echo "    make eval-quality       Lance une évaluation qualité"
	@echo "    make eval-drift         Détecte une dérive comportementale"
	@echo "    make run-eval-cron      Lance l'évaluation automatique manuellement"
	@echo "    make install-eval-cron  Installe le cron launchd (quotidien à 2h00)"
	@echo ""
	@echo "  Déploiement"
	@echo "    make start              Démarre tout l'environnement"
	@echo "    make stop               Arrête tous les services"
	@echo "    make healthcheck        Vérifie l'état de tous les services"
	@echo "    make install-service    Installe le service launchd (une fois)"
	@echo ""
	@echo "  Divers"
	@echo "    make clean              Supprime le venv et les caches"
	@echo "    make logs               Affiche les logs de l'API"
	@echo ""

# ── Setup ─────────────────────────────────────────────────────────────────────

setup: $(VENV)/bin/activate install
	@$(VENV)/bin/pre-commit install
	@echo "✓ Projet prêt. Copie .env.example → .env et remplis ta clé OPENROUTER_API_KEY."

$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)

install: $(VENV)/bin/activate
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	$(PIP) install pre-commit

# ── Docker ────────────────────────────────────────────────────────────────────

docker-up:
	docker compose -f infra/docker/docker-compose.yml up -d
	@echo "✓ Qdrant sur http://localhost:6333 | PostgreSQL sur localhost:5432 | n8n sur http://localhost:5678"

docker-down:
	docker compose -f infra/docker/docker-compose.yml down

docker-logs:
	docker compose -f infra/docker/docker-compose.yml logs -f

# ── Agents (terminal) ────────────────────────────────────────────────────────

dev-senior:
	$(VENV)/bin/python -m agents.dev_senior

biz-manager:
	$(VENV)/bin/python -m agents.biz_manager

# ── Frontend React ────────────────────────────────────────────────────────────

frontend-install:
	cd frontend && npm install

frontend-env:
	@if [ ! -f frontend/.env.local ]; then \
		cp frontend/.env.example frontend/.env.local; \
		echo "✓ frontend/.env.local créé — remplir VITE_API_KEY avant de builder"; \
	else \
		echo "frontend/.env.local existe déjà"; \
	fi

frontend:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

# ── Qualité ──────────────────────────────────────────────────────────────────

test:
	$(PYTEST) tests/ -v

test-watch:
	$(PYTEST) tests/ -v --tb=short -f

lint:
	$(RUFF) check .

format:
	$(RUFF) format .
	$(RUFF) check --fix .

typecheck:
	$(MYPY) agents/ --ignore-missing-imports

check: lint typecheck test
	@echo "✓ Tout est propre."

# ── API HTTP & n8n ───────────────────────────────────────────────────────────

api:
	$(VENV)/bin/uvicorn api.main:app --host 0.0.0.0 --port $${PORT:-8080} --reload

api-prod:
	$(VENV)/bin/uvicorn api.main:app --host 0.0.0.0 --port $${PORT:-8080} --workers 2

serve-prod: frontend-build api-prod

n8n:
	open http://localhost:5678

# ── Mémoire ──────────────────────────────────────────────────────────────────

index-codebase:
	$(VENV)/bin/python -m memory.dev_senior.indexer .

index-codebase-force:
	$(VENV)/bin/python -m memory.dev_senior.indexer . --force

# ── Observabilité & Evals ────────────────────────────────────────────────────

eval-quality:
	$(VENV)/bin/python -m observability.evals.eval_quality $(ARGS)

eval-drift:
	$(VENV)/bin/python -m observability.evals.eval_drift $(ARGS)

eval-set-baseline:
	$(VENV)/bin/python -m observability.evals.eval_drift --set-baseline $(ARGS)

run-eval-cron:
	$(VENV)/bin/python -m observability.evals.cron_eval

install-eval-cron:
	@chmod +x infra/deploy/install_eval_cron.sh && bash infra/deploy/install_eval_cron.sh

# ── MCP Servers (tests isolés) ────────────────────────────────────────────────

test-github:
	$(PYTEST) tests/mcp_servers/test_github.py -v

test-mcp:
	$(PYTEST) tests/mcp_servers/ -v

mcp-github:
	$(VENV)/bin/python -m mcp_servers.github.server

mcp-google:
	$(VENV)/bin/python -m mcp_servers.google_workspace.server

mcp-crm:
	$(VENV)/bin/python -m mcp_servers.crm.server

mcp-seo:
	$(VENV)/bin/python -m mcp_servers.seo.server

# ── Déploiement ──────────────────────────────────────────────────────────────

start:
	@chmod +x infra/deploy/start.sh && bash infra/deploy/start.sh

stop:
	@chmod +x infra/deploy/stop.sh && bash infra/deploy/stop.sh

healthcheck:
	@chmod +x infra/deploy/healthcheck.sh && bash infra/deploy/healthcheck.sh

install-service:
	@chmod +x infra/deploy/install_launchd.sh && bash infra/deploy/install_launchd.sh

logs:
	@tail -f logs/api.log

logs-error:
	@tail -f logs/api-error.log

deploy: check install
	@echo "Déploiement terminé. Lance 'make start' pour démarrer."

# ── Divers ───────────────────────────────────────────────────────────────────

clean:
	rm -rf $(VENV) .mypy_cache .ruff_cache .pytest_cache __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
