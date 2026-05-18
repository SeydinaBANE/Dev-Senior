# Guide — Agent Dev Senior

**Pour l'équipe technique**

---

## C'est quoi ?

Dev Senior est un agent IA qui connaît votre codebase et agit comme un membre permanent de l'équipe. Il peut faire des code reviews, débugger, proposer des architectures, et rédiger de la documentation — en gardant le contexte de la conversation.

---

## Démarrage rapide

```bash
# Terminal, dans le dossier du projet
make dev-senior
```

Si tu veux utiliser Claude API au lieu d'Ollama local :
```bash
make dev-senior-cloud
```

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

## Fonctionnement de la mémoire

L'agent **cherche automatiquement** dans la codebase indexée avant de répondre. Pour que ça fonctionne :

```bash
# Indexer le projet (à refaire après des changements majeurs)
make index-codebase

# Forcer la réindexation complète
make index-codebase-force
```

La mémoire persiste entre les sessions — l'agent se souvient du contexte codebase même après un redémarrage.

---

## Utilisation via l'API (pour intégrations)

```bash
curl -X POST http://localhost:8080/dev-senior/chat \
  -H "Content-Type: application/json" \
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
  -d '{"message": "Et comment améliorer la gestion des erreurs ?", "session_id": "abc123"}'
```

---

## Modèles disponibles

| Mode | Modèle | Latence | Usage |
|---|---|---|---|
| Local (défaut) | qwen2.5-coder:7b via Ollama | ~5-15s | Usage quotidien |
| Cloud | claude-sonnet-4-6 | ~2-5s | Tâches complexes |

Passer en cloud : `USE_CLOUD=true make dev-senior`

---

## Surveillance

```bash
# Vérifier que tout tourne
make healthcheck

# Voir les traces Logfire (si token configuré)
# → https://logfire.pydantic.dev

# Évaluation qualité
make eval-quality ARGS="--agent dev-senior --samples-file tests/samples/dev_senior.json"
```

---

## Problèmes courants

**L'agent répond lentement**
→ Normal en mode Docker CPU. Utiliser `make dev-senior-cloud` pour les tâches urgentes.

**"Ollama ne répond pas"**
→ `make docker-up` puis attendre 30s.

**La mémoire ne trouve pas le bon fichier**
→ Relancer `make index-codebase` après avoir ajouté des fichiers.

**Erreur MCP GitHub**
→ Vérifier que `GITHUB_TOKEN` est dans `.env` avec les bons scopes (`repo`).
