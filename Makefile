.DEFAULT_GOAL := help
SHELL := /bin/bash
PYTHON := python3
VENV := .venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
MYPY := $(VENV)/bin/mypy
RUFF := $(VENV)/bin/ruff

.PHONY: help setup install dev docker-up docker-down models dev-senior biz-manager test lint typecheck format clean

# ── Aide ─────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "  Dev Senior & Business Manager — Commandes disponibles"
	@echo ""
	@echo "  Setup"
	@echo "    make setup        Crée le venv et installe toutes les dépendances"
	@echo "    make install      Installe uniquement les dépendances (venv existant)"
	@echo ""
	@echo "  Docker"
	@echo "    make docker-up    Démarre Ollama + ChromaDB"
	@echo "    make docker-down  Arrête les containers"
	@echo "    make models       Télécharge les modèles LLM dans Ollama"
	@echo ""
	@echo "  Agents"
	@echo "    make dev-senior   Lance l'agent Dev Senior (chat)"
	@echo "    make biz-manager  Lance l'agent Business Manager (chat)"
	@echo ""
	@echo "  Qualité"
	@echo "    make test         Lance tous les tests"
	@echo "    make lint         Vérifie le style avec ruff"
	@echo "    make format       Formate le code avec ruff"
	@echo "    make typecheck    Vérifie les types avec mypy"
	@echo "    make check        lint + typecheck + test"
	@echo ""
	@echo "  Divers"
	@echo "    make clean        Supprime le venv et les caches"
	@echo ""

# ── Setup ─────────────────────────────────────────────────────────────────────

setup: $(VENV)/bin/activate install
	@$(VENV)/bin/pre-commit install
	@echo "✓ Projet prêt. Copie .env.example → .env et remplis tes clés API."

$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)

install: $(VENV)/bin/activate
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	$(PIP) install pre-commit

# ── Docker ────────────────────────────────────────────────────────────────────

docker-up:
	docker compose -f infra/docker/docker-compose.yml up -d
	@echo "✓ Ollama sur http://localhost:11434 | ChromaDB sur http://localhost:8000"

docker-down:
	docker compose -f infra/docker/docker-compose.yml down

docker-logs:
	docker compose -f infra/docker/docker-compose.yml logs -f

models:
	@chmod +x infra/docker/pull-models.sh
	@infra/docker/pull-models.sh

# ── Agents ───────────────────────────────────────────────────────────────────

dev-senior:
	$(VENV)/bin/python -m agents.dev_senior

biz-manager:
	$(VENV)/bin/python -m agents.biz_manager

# Mode cloud (Claude API au lieu d'Ollama)
dev-senior-cloud:
	USE_CLOUD=true $(VENV)/bin/python -m agents.dev_senior

biz-manager-cloud:
	USE_CLOUD=true $(VENV)/bin/python -m agents.biz_manager

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

# ── Divers ───────────────────────────────────────────────────────────────────

clean:
	rm -rf $(VENV) .mypy_cache .ruff_cache .pytest_cache __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
