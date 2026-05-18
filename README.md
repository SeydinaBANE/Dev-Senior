# Agents IA Internes — Dev Senior & Business Manager

Deux agents IA déployés en interne pour augmenter la productivité de l'équipe technique et des business managers.

---

## Les deux agents

### Agent #1 — Dev Senior
Un assistant technique permanent intégré à l'équipe de développement.

**Utilisateurs** : équipe technique  
**Capacités** : développement complexe, architecture logicielle, debugging, code reviews, refactoring, documentation technique  
**Modèle** : Claude API (priorité) + Qwen 2.5 Coder via Ollama (local)

### Agent #2 — Business Manager
Un assistant pour les profils non techniques, conçu pour l'autonomie et la productivité.

**Utilisateurs** : business managers, stagiaires  
**Capacités** : création de sites via Claude Code, marketing digital, SEO, réseaux sociaux, production de contenu, automatisation des workflows  
**Modèle** : Claude API (priorité) + Llama 3.1 via Ollama (local)

---

## Architecture

```
┌─────────────────────────────────────────────┐
│             Agents (Pydantic AI)            │
│  ┌──────────────────┐  ┌─────────────────┐  │
│  │   Dev Senior     │  │  Biz Manager    │  │
│  │  Claude/Qwen     │  │  Claude/Llama   │  │
│  └────────┬─────────┘  └────────┬────────┘  │
└───────────┼─────────────────────┼───────────┘
            │         MCP         │
┌───────────▼─────────────────────▼───────────┐
│            MCP Servers (custom)             │
│   GitHub | Google WS | CRM | SEO | n8n     │
└─────────────────────────────────────────────┘
            │
┌───────────▼─────────────────────────────────┐
│        Inférence locale (Mac mini M4)       │
│           Ollama  /  MLX                    │
└─────────────────────────────────────────────┘
```

---

## Stack technique

| Composant | Technologie | Justification |
|---|---|---|
| Orchestration agents | Pydantic AI | Type-safe, multi-provider, testable |
| LLMs cloud | Claude API, OpenAI API | Qualité maximale |
| LLMs locaux | Ollama (Qwen, Llama) | Latence faible, données sensibles |
| Inférence Apple Silicon | MLX ou Ollama | Optimisation Mac mini M4 |
| Intégrations | MCP (custom servers) | Standard ouvert, extensible |
| Mémoire long terme | ChromaDB (local) | Vecteurs, requêtes sémantiques |
| Observabilité | Logfire | Tracing natif Pydantic AI |
| Workflows | n8n | Low-code, accessible non-tech |
| Infra | Docker, Git | Reproductibilité |

---

## Installation

### Prérequis

- Mac mini M4 (ou tout Mac Apple Silicon)
- Python 3.11+
- [Ollama](https://ollama.ai)
- Docker (optionnel pour les services annexes)

### Setup

```bash
# 1. Cloner le dépôt
git clone <repo-url>
cd Dev-Senior

# 2. Environnement Python
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Variables d'environnement
cp .env.example .env
# Éditer .env avec vos clés API

# 4. Installer les modèles locaux
ollama pull qwen2.5-coder    # pour Dev Senior
ollama pull llama3.1         # pour Business Manager

# 5. Lancer Ollama
ollama serve
```

### Premier démarrage

```bash
# Agent Dev Senior
python -m agents.dev_senior.agent

# Agent Business Manager
python -m agents.biz_manager.agent
```

---

## Structure du projet

```
Dev-Senior/
├── CLAUDE.md              ← instructions pour Claude Code
├── README.md              ← ce fichier
├── TODO.md                ← feuille de route
├── agents/
│   ├── dev_senior/        ← Agent Dev Senior
│   └── biz_manager/       ← Agent Business Manager
├── mcp_servers/
│   ├── github/            ← intégration GitHub
│   ├── google_workspace/  ← Drive, Gmail, Calendar
│   ├── crm/               ← CRM interne
│   └── seo/               ← outils SEO
├── memory/                ← base vectorielle locale
├── observability/         ← tracing et évaluations
├── workflows/n8n/         ← exports de workflows
├── infra/                 ← scripts de setup
├── tests/                 ← tests unitaires et intégration
└── docs/                  ← documentation technique
```

---

## Observabilité

Les traces et logs sont gérés via **Logfire** (Pydantic). Configurer dans `observability/logfire_config.py`.

Métriques suivies :
- Latence P50/P95 par agent et par modèle
- Taux d'erreur et fallbacks
- Qualité des réponses (eval continue)
- Dérive de comportement

---

## Contribuer

1. Créer une branche depuis `main`
2. Implémenter et tester localement (`pytest tests/`)
3. Vérifier les types (`mypy`)
4. Ouvrir une PR avec description et métriques de latence si changement de modèle
