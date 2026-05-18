# TODO — Feuille de route

Dernière mise à jour : 2026-05-18

---

## Phase 1 — Infrastructure & PoC

Objectif : avoir un agent fonctionnel de bout en bout en local.

- [x] Configurer `pyproject.toml` avec toutes les dépendances
- [x] Écrire le `.env.example`
- [x] `infra/docker/docker-compose.yml` — Ollama + ChromaDB via Docker
- [x] `infra/docker/pull-models.sh` — script de téléchargement des modèles
- [x] Créer l'agent Dev Senior (Pydantic AI + Ollama)
- [x] Créer l'agent Business Manager (Pydantic AI + Ollama)
- [x] Tests de smoke (sans appel réseau, via TestModel)
- [ ] Lancer `docker compose up -d` et vérifier que Ollama répond
- [ ] Exécuter `./infra/docker/pull-models.sh` pour télécharger les modèles
- [ ] Installer les dépendances Python : `pip install -e ".[dev]"`
- [ ] Tester un agent en live : `python -m agents.dev_senior`
- [ ] Comparer latence Claude API vs Ollama Docker (P50/P95)
- [ ] Décision : garder Docker ou passer à Ollama natif selon les perfs

---

## Phase 2 — MCP Servers

Objectif : brancher les agents aux outils internes.

- [ ] MCP server GitHub (priorité Dev Senior)
  - [ ] Lister les PRs ouvertes
  - [ ] Lire les fichiers d'un dépôt
  - [ ] Créer des issues
- [ ] MCP server Google Workspace (priorité Biz Manager)
  - [ ] Google Drive (lire, créer des fichiers)
  - [ ] Gmail (lire, envoyer)
  - [ ] Google Calendar (lire, créer des événements)
- [ ] MCP server CRM interne
  - [ ] À définir selon le CRM utilisé
- [ ] MCP server outils SEO
  - [ ] À définir (Search Console, SEMrush, etc.)
- [ ] Tests d'intégration pour chaque MCP server
- [ ] Documentation d'utilisation de chaque serveur

---

## Phase 3 — Mémoire & Observabilité

Objectif : mémoire long terme et visibilité production.

- [ ] Choisir la base vectorielle : ChromaDB vs Qdrant
- [ ] Implémenter la mémoire court terme (contexte de conversation)
- [ ] Implémenter la mémoire long terme (faits persistants sur la codebase)
- [ ] Indexer la codebase dans la mémoire de l'agent Dev Senior
- [ ] Configurer Logfire pour le tracing
- [ ] Définir les métriques de dérive à surveiller
- [ ] Créer les premiers scripts d'évaluation (`observability/evals/`)
- [ ] Mettre en place les guardrails (contenu, scope, sécurité)

---

## Phase 4 — Workflows n8n

Objectif : automatiser les workflows business via l'agent Biz Manager.

- [ ] Installer n8n (Docker ou cloud)
- [ ] Identifier les 3-5 workflows prioritaires avec les business managers
- [ ] Workflow #1 : (à définir)
- [ ] Workflow #2 : (à définir)
- [ ] Workflow #3 : (à définir)
- [ ] Connecter n8n à l'agent Business Manager
- [ ] Exporter et versionner les workflows dans `workflows/n8n/`

---

## Phase 5 — Formation & Déploiement

Objectif : mise en production et adoption par les équipes.

- [x] Documentation utilisateur pour l'équipe tech (`docs/guide_dev_senior.md`)
- [x] Documentation utilisateur pour les stagiaires (`docs/guide_biz_manager.md`)
- [x] CI/CD GitHub Actions (lint + types + tests + scan secrets)
- [x] Pipeline de déploiement sur runner self-hosted Mac mini M4
- [x] Scripts de démarrage/arrêt (`infra/deploy/start.sh`, `stop.sh`)
- [x] Health check automatisé (`infra/deploy/healthcheck.sh`)
- [x] Service launchd pour l'API (redémarrage automatique au boot)
- [ ] Installer le runner GitHub Actions sur le Mac mini M4
- [ ] Configurer `make install-service` sur la machine cible
- [ ] Sessions de formation (équipe tech + business managers)
- [ ] Recueil des premiers retours utilisateurs
- [ ] Backlog d'itérations v1.1

---

## Backlog (idées futures)

- Évaluation automatique de la qualité des réponses (LLM-as-judge)
- Multi-agent : faire collaborer Dev Senior et Biz Manager
- Interface web légère pour les non-tech (au lieu du terminal)
- Support des modèles MLX natifs Apple Silicon
- Intégration Slack/Teams pour accéder aux agents depuis le chat
