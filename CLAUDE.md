# Dev-Senior — Instructions pour Claude Code

## Contexte du projet

Ce dépôt contient deux agents IA internes :

- **Dev Senior** (`agents/dev_senior/`) : assistant technique permanent pour l'équipe dev. Il connaît la codebase et agit comme un membre de l'équipe (debugging, archi, code reviews, refactoring, doc technique).
- **Business Manager** (`agents/biz_manager/`) : assistant pour les profils non techniques (création de sites, marketing, SEO, réseaux sociaux, automatisation de workflows).

## Stack technique

- **Orchestration** : Pydantic AI
- **LLMs** : Claude API (prod) + Ollama/MLX (local, Mac mini M4)
- **Intégrations** : MCP (Model Context Protocol) — serveurs custom dans `mcp_servers/`
- **Mémoire** : base vectorielle locale dans `memory/vector_store/`
- **Observabilité** : Logfire (`observability/logfire_config.py`)
- **Workflows** : n8n (exports dans `workflows/n8n/`)

## Conventions de code

- Python 3.11+ avec type hints stricts
- Pydantic AI pour la définition des agents et des tools
- Un fichier par responsabilité (`agent.py`, `prompts.py`, `memory.py`)
- Tests dans `tests/agents/` et `tests/mcp_servers/`
- Variables d'environnement via `.env` (ne jamais committer les secrets)

## Commandes importantes

```bash
# Lancer Ollama (Mac mini M4)
ollama serve

# Lancer un agent en mode dev
python -m agents.dev_senior.agent

# Lancer les tests
pytest tests/

# Vérifier les types
mypy agents/ mcp_servers/
```

## Structure de la codebase

```
agents/          ← implémentations des agents (Pydantic AI)
mcp_servers/     ← serveurs MCP custom (GitHub, Google WS, CRM, SEO)
memory/          ← base vectorielle pour la mémoire long terme
observability/   ← tracing Logfire + scripts d'évaluation
workflows/       ← exports n8n
infra/           ← scripts de setup (Ollama, Docker)
tests/           ← tests unitaires et d'intégration
docs/            ← documentation technique (ADR, guides)
```

## Règles importantes

- Ne jamais hardcoder les clés API — utiliser `.env`
- Tester chaque MCP server de façon isolée avant de le brancher à un agent
- Documenter les décisions architecturales dans `docs/adr/`
- Mesurer la latence (P50/P95) à chaque changement de modèle
