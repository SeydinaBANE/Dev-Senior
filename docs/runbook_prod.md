# Runbook — Mise en production (Mac mini M4)

**À faire une seule fois sur la machine cible.**

---

## Prérequis

- [ ] Mac mini M4 avec macOS 14+
- [ ] Python 3.11+ (`python3 --version`)
- [ ] Node.js 20+ (`node --version`)
- [ ] Docker Desktop installé et lancé
- [ ] Git configuré (`git config --global user.email`)
- [ ] Accès aux clés API : OpenRouter, Langfuse, GitHub, HubSpot, Google

---

## Étape 1 — Cloner le dépôt

```bash
git clone https://github.com/SeydinaBANE/Dev-Senior.git
cd Dev-Senior
```

---

## Étape 2 — Variables d'environnement

```bash
cp .env.example .env
```

Remplir **toutes** les valeurs obligatoires dans `.env` :

| Variable | Où la trouver |
|---|---|
| `OPENROUTER_API_KEY` | https://openrouter.ai/keys |
| `AGENTS_API_KEY` | Générer : `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `POSTGRES_PASSWORD` | Choisir un mot de passe fort |
| `LANGFUSE_PUBLIC_KEY` | https://cloud.langfuse.com → Settings → API Keys |
| `LANGFUSE_SECRET_KEY` | idem |
| `GITHUB_TOKEN` | https://github.com/settings/tokens (scope : `repo`) |
| `GOOGLE_CREDENTIALS_FILE` | Télécharger depuis Google Cloud Console |
| `CRM_API_KEY` | HubSpot → Settings → Integrations → Private Apps |
| `SLACK_SIGNING_SECRET` | https://api.slack.com/apps → Basic Information |
| `TEAMS_WEBHOOK_KEY` | Fourni lors de la création du webhook Teams |
| `N8N_PASSWORD` | Choisir un mot de passe fort |

Optionnel (sessions rapides) :
```
REDIS_URL=redis://localhost:6379/0
```

---

## Étape 3 — Setup Python

```bash
make setup
```

---

## Étape 4 — Démarrer l'infrastructure Docker

```bash
make docker-up
```

Vérifier que les containers tournent :
```bash
docker ps
# Doit afficher : qdrant, postgres, redis, n8n
```

---

## Étape 5 — Installer le service launchd (démarrage au boot)

```bash
make install-service
```

Ce script :
1. Vérifie que `.env` existe
2. Installe `com.agents.api.plist` dans `~/Library/LaunchAgents/`
3. Démarre l'API immédiatement

Vérifier :
```bash
launchctl list com.agents.api
# Doit afficher le PID (pas 0)
```

---

## Étape 6 — Build et vérification du frontend

```bash
make frontend-install
make frontend-env
# → Éditer frontend/.env.local : VITE_API_KEY = valeur de AGENTS_API_KEY dans .env
make frontend-build
```

L'interface est disponible sur http://localhost:8080/app

---

## Étape 7 — Healthcheck global

```bash
make healthcheck
```

Tout doit afficher ✓. En cas d'erreur, voir la section Dépannage.

---

## Étape 8 — Indexer la codebase (mémoire Dev Senior)

```bash
make index-codebase
```

Durée : 2-5 minutes selon la taille du projet.

---

## Étape 9 — Fixer la baseline qualité

```bash
make eval-set-baseline
```

Nécessite des clés Langfuse valides et au moins quelques traces enregistrées.

---

## Étape 10 — Installer le cron d'évaluation quotidienne

```bash
make install-eval-cron
```

Tournera chaque nuit à 2h, évaluera les agents, poussera les scores dans Langfuse.

---

## Étape 11 — Runner GitHub Actions

Pour activer le déploiement automatique (`git push` → deploy) :

1. Aller sur https://github.com/SeydinaBANE/Dev-Senior/settings/actions/runners
2. Cliquer **New self-hosted runner** → macOS → suivre les instructions
3. Lancer le runner en tant que service :
   ```bash
   ./svc.sh install
   ./svc.sh start
   ```
4. Dans GitHub → Settings → Secrets → Actions, ajouter :
   - `VITE_API_KEY` = valeur de `AGENTS_API_KEY`
   - `VITE_API_URL` = laisser vide si l'API est sur le même hôte

---

## Étape 12 — Activer les workflows n8n

1. Ouvrir http://localhost:5678
2. Login : `admin` / mot de passe défini dans `.env`
3. Importer les workflows depuis `workflows/n8n/`
4. Configurer les credentials pour chaque workflow (Google, HubSpot, email…)
5. Activer les workflows un par un

---

## Récapitulatif des URLs

| Service | URL |
|---|---|
| Interface web agents | http://localhost:8080/app |
| API (Swagger) | http://localhost:8080/docs |
| API health | http://localhost:8080/health |
| API métriques | http://localhost:8080/metrics |
| Qdrant dashboard | http://localhost:6333/dashboard |
| n8n | http://localhost:5678 |
| Langfuse | https://cloud.langfuse.com |

---

## Commandes du quotidien

```bash
make start          # tout démarrer après un reboot
make stop           # tout arrêter proprement
make healthcheck    # vérifier l'état des services
make deploy         # mettre à jour après un git pull
make logs           # suivre les logs de l'API en temps réel
make logs-error     # logs d'erreurs uniquement
```

---

## Dépannage

**L'API ne démarre pas**
```bash
tail -50 logs/api-error.log
# Causes fréquentes : .env manquant, OPENROUTER_API_KEY invalide, PostgreSQL pas encore prêt
```

**PostgreSQL connexion refusée**
```bash
docker logs postgres --tail 20
# Si "FATAL: password authentication failed" → vérifier POSTGRES_PASSWORD dans .env
```

**Qdrant non joignable**
```bash
docker logs qdrant --tail 20
make docker-up  # relancer si stoppé
```

**L'interface web (/app) affiche une page blanche**
```bash
make frontend-build  # rebuilder si les assets sont manquants
# Vérifier que frontend/dist/ existe
```

**Slack slash command ne répond pas**
→ Vérifier `SLACK_SIGNING_SECRET` dans `.env` et que l'API est accessible depuis l'internet (ngrok ou domaine public nécessaire).

**Le cron d'évaluation ne tourne pas**
```bash
launchctl list com.agents.eval
tail -20 logs/eval_$(date +%Y-%m-%d).log
```
