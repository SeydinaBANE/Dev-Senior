# Guide — Agent Dev Senior

**Pour l'équipe technique**

---

## C'est quoi ?

Dev Senior est un agent IA qui connaît votre codebase et agit comme un membre permanent de l'équipe. Il peut faire des code reviews, débugger, proposer des architectures, et rédiger de la documentation — en gardant le contexte de la conversation.

Il partage aussi une mémoire commune avec le Business Manager : les décisions métier importantes prises avec lui sont automatiquement disponibles dans son contexte.

---

## Démarrage rapide

**Option 1 — Interface web (recommandé)**

```bash
make api           # démarre l'API (port 8080)
make frontend      # démarre le frontend → http://localhost:5173
```

Sélectionner **Dev Senior** dans la barre latérale.

**Option 2 — Terminal**

```bash
make dev-senior
```

**Option 3 — Slack**

```
/dev-senior Explique-moi comment fonctionne api/sessions.py
```
→ Réponse postée dans le canal dans les quelques secondes.

---

## Ce que tu peux lui demander

### Code review
```
Toi > Regarde ce fichier agents/dev_senior/agent.py et dis-moi ce que tu améliorerais
```

### Debugging
```
Toi > J'ai cette erreur : AttributeError: 'NoneType' object has no attribute 'run'
      C'est dans __main__.py ligne 24. Le contexte c'est...
```

### Architecture
```
Toi > On veut ajouter un système de guardrails pour filtrer les réponses dangereuses.
      Comment tu structurerais ça dans le projet actuel ?
```

### GitHub (via MCP)
```
Toi > Liste-moi les PRs ouvertes sur le repo owner/repo
Toi > Lis le fichier src/auth.py sur la branche main
Toi > Crée une issue "Ajouter les tests d'intégration MCP" avec le label "testing"
```

### Documentation
```
Toi > Rédige la docstring de la fonction retrieve_context dans memory/dev_senior/retriever.py
```

---

## Dashboard métriques

L'onglet **Dashboard** du frontend affiche en temps réel :
- Latence P50 et P95 par agent
- Taux d'erreur
- Scores de qualité LLM-as-judge (note sur 10)

Ou directement via l'API :
```bash
curl http://localhost:8080/metrics -H "X-API-Key: votre-cle"
```

---

## Fonctionnement de la mémoire

L'agent **cherche automatiquement** dans la codebase indexée + le contexte partagé avec le Biz Manager avant de répondre.

Pour que ça fonctionne :

```bash
# Indexer le projet (à refaire après des changements majeurs)
make index-codebase

# Forcer la réindexation complète
make index-codebase-force
```

La mémoire est stockée dans Qdrant (dashboard : http://localhost:6333/dashboard) — elle persiste entre les sessions.

**Collections Qdrant :**
| Collection | Contenu |
|---|---|
| `codebase` | Fichiers du projet indexés par Dev Senior |
| `shared` | Contexte partagé entre Dev Senior et Business Manager |

---

## Utilisation via l'API (pour intégrations)

```bash
curl -X POST http://localhost:8080/dev-senior/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: votre-cle-api" \
  -d '{"message": "Explique-moi le fichier api/main.py"}'
```

Réponse :
```json
{
  "response": "Le fichier api/main.py définit...",
  "session_id": "abc123"
}
```

Pour continuer la conversation, réutiliser le même `session_id` :
```bash
curl -X POST http://localhost:8080/dev-senior/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: votre-cle-api" \
  -d '{"message": "Et comment améliorer la gestion des erreurs ?", "session_id": "abc123"}'
```

---

## Modèles

| Mode | Modèle | Fournisseur |
|---|---|---|
| Défaut | `qwen/qwen-2.5-coder-7b-instruct` | OpenRouter |
| Changer | `DEV_SENIOR_MODEL=autre/modele` dans `.env` | OpenRouter |

Pour changer de modèle, modifier `DEV_SENIOR_MODEL` dans `.env`. Tous les modèles disponibles : https://openrouter.ai/models

---

## Observabilité

```bash
# Vérifier que tout tourne
make healthcheck

# Voir les traces dans Langfuse
# → https://cloud.langfuse.com (ou LANGFUSE_HOST si self-hosted)

# Évaluation qualité manuelle
make eval-quality

# Détecter une dérive de comportement
make eval-drift

# Le cron tourne automatiquement chaque nuit à 2h si installé
make install-eval-cron
```

---

## Problèmes courants

**L'agent répond lentement**
→ Normal pour les modèles 7B-8B. Changer `DEV_SENIOR_MODEL` pour un modèle plus rapide/puissant sur OpenRouter.

**"Qdrant ne répond pas"**
→ `make docker-up` puis attendre 15s.

**"PostgreSQL connexion refusée"**
→ `make docker-up`. Vérifier `DATABASE_URL` dans `.env`.

**La mémoire ne trouve pas le bon fichier**
→ Relancer `make index-codebase` après avoir ajouté des fichiers.

**Erreur MCP GitHub**
→ Vérifier que `GITHUB_TOKEN` est dans `.env` avec les bons scopes (`repo`).

**Slash command Slack ne répond pas**
→ Vérifier que `SLACK_SIGNING_SECRET` est défini et correspond à celui de la Slack App.
