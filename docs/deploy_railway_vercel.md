# Déploiement Railway (API) + Vercel (Frontend)

Ce guide couvre le déploiement cloud de l'application :
- **Railway** héberge l'API FastAPI + PostgreSQL + Redis + Qdrant
- **Vercel** héberge le frontend React

```
Utilisateurs
    │
    ├─→ Vercel  (frontend React, HTTPS)
    │         │ VITE_API_URL → Railway
    │
    └─→ Railway (API FastAPI :PORT)
              ├─ PostgreSQL  (plugin Railway)
              ├─ Redis        (plugin Railway)
              └─ Qdrant       (service Railway ou Qdrant Cloud)
```

---

## 1. Prérequis

- Compte [Railway](https://railway.app) (plan Hobby minimum — $5/mo)
- Compte [Vercel](https://vercel.com) (plan gratuit suffisant)
- Compte [Qdrant Cloud](https://cloud.qdrant.io) (cluster gratuit 1 GB)
- Dépôt GitHub connecté aux deux plateformes

---

## 2. Déploiement Railway (API)

### 2.1 Créer le projet

1. Railway → **New Project** → **Deploy from GitHub repo** → sélectionner `Dev-Senior`
2. Railway détecte le `Dockerfile` dans `infra/docker/` et l'utilise automatiquement (prioritaire sur Nixpacks)
3. Le `railway.toml` existe comme fallback si Dockerfile n'est pas détecté

### 2.2 Ajouter les services de données

Dans le projet Railway, cliquer **New** pour chaque service :

| Service | Comment l'ajouter |
|---|---|
| **PostgreSQL** | New → Database → PostgreSQL |
| **Redis** | New → Database → Redis |
| **Qdrant** | New → Docker Image → `qdrant/qdrant:latest` |

Pour **Qdrant** (service Docker) :
- Variables d'environnement : aucune requise
- Volume : monter `/qdrant/storage` pour la persistance
- Port exposé : `6333`

> **Alternative** : utiliser [Qdrant Cloud](https://cloud.qdrant.io) (cluster gratuit, moins de configuration). Dans ce cas, récupérer `QDRANT_HOST` et `QDRANT_API_KEY` depuis le dashboard Qdrant Cloud.

### 2.3 Variables d'environnement Railway

Dans le service API → **Variables**, ajouter :

```bash
# === Obligatoires ===
OPENROUTER_API_KEY=sk-or-v1-...
AGENTS_API_KEY=<générer avec: python3 -c "import secrets; print(secrets.token_urlsafe(32))">
DOCS_ENABLED=false

# === Base de données ===
# Railway injecte DATABASE_URL automatiquement depuis le plugin PostgreSQL
# Railway injecte REDIS_URL automatiquement depuis le plugin Redis
# Vérifier que ces variables sont bien référencées depuis les plugins :
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}

# === Qdrant ===
# Option A — service Railway interne :
QDRANT_HOST=${{qdrant.RAILWAY_PRIVATE_DOMAIN}}
QDRANT_PORT=6333
# Option B — Qdrant Cloud :
# QDRANT_HOST=<cluster-id>.<region>.cloud.qdrant.io
# QDRANT_PORT=6333
# QDRANT_API_KEY=<votre-clé-qdrant-cloud>

# === Modèles ===
DEV_SENIOR_MODEL=qwen/qwen-2.5-coder-7b-instruct
BIZ_MANAGER_MODEL=meta-llama/llama-3.1-8b-instruct
EMBED_MODEL=openai/text-embedding-3-small

# === Sessions ===
SESSION_TTL_SECONDS=3600

# === CORS (ajouter l'URL Vercel après déploiement) ===
CORS_ORIGINS=https://<votre-app>.vercel.app

# === Observabilité ===
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# === MCP GitHub (optionnel) ===
GITHUB_TOKEN=ghp_...

# === Slack / Teams (optionnel) ===
SLACK_SIGNING_SECRET=
TEAMS_WEBHOOK_KEY=
```

> Railway injecte automatiquement `PORT` — ne pas le définir manuellement.

### 2.4 Domaine public

Service API → **Settings** → **Networking** → **Generate Domain**
→ noter l'URL publique, ex. `https://dev-senior-api.up.railway.app`

### 2.5 Vérifier le déploiement

```bash
curl https://dev-senior-api.up.railway.app/dev-senior/health
# → {"status": "ok", "agent": "dev-senior"}
```

---

## 3. Déploiement Vercel (Frontend)

### 3.1 Importer le projet

1. Vercel → **Add New Project** → importer le dépôt GitHub `Dev-Senior`
2. **Root Directory** : `frontend`
3. **Framework Preset** : Vite (détecté automatiquement)
4. **Build Command** : `npm run build` (défaut)
5. **Output Directory** : `dist` (défaut)

### 3.2 Variables d'environnement Vercel

Dans **Settings → Environment Variables** :

| Variable | Valeur | Environnements |
|---|---|---|
| `VITE_API_URL` | `https://dev-senior-api.up.railway.app` | Production, Preview |
| `VITE_API_KEY` | Même valeur que `AGENTS_API_KEY` sur Railway | Production, Preview |
| `VITE_BASE_PATH` | `/` | Production, Preview |

> `VITE_BASE_PATH=/` est obligatoire sur Vercel — Vercel sert le frontend depuis la racine `/`, pas depuis `/app/` comme FastAPI en self-hosted.

### 3.3 Lancer le déploiement

**Deployments** → **Redeploy** (ou pusher sur `main` déclenche un déploiement automatique).

Le `frontend/vercel.json` contient la règle de rewrite SPA :
```json
{ "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }
```

### 3.4 Vérifier le déploiement

Ouvrir `https://<votre-app>.vercel.app` — le frontend doit se connecter à l'API Railway.

---

## 4. Compléter la configuration CORS

Après avoir l'URL Vercel, mettre à jour la variable Railway :

```
CORS_ORIGINS=https://<votre-app>.vercel.app,https://votre-domaine.com
```

Railway redéploie automatiquement.

---

## 5. Indexer la codebase dans Qdrant

L'indexation RAG ne se fait pas automatiquement au déploiement.
Depuis la machine locale (avec `QDRANT_HOST` pointant sur Railway/Qdrant Cloud) :

```bash
# Pointer sur le Qdrant distant
export QDRANT_HOST=dev-senior-api.up.railway.app  # ou cluster Qdrant Cloud
export QDRANT_PORT=6333

make index-codebase
```

---

## 6. MCP Servers en prod

Les MCP Servers (GitHub, Google Workspace, CRM, SEO) utilisent `MCPServerStdio` — ils sont lancés comme sous-processus au démarrage de l'API. Ils fonctionnent sur Railway sans configuration supplémentaire si les variables d'environnement correspondantes sont définies (`GITHUB_TOKEN`, `GOOGLE_CREDENTIALS_FILE`, etc.).

> `GOOGLE_CREDENTIALS_FILE` nécessite un fichier local. Sur Railway, utiliser une variable `GOOGLE_CREDENTIALS_JSON` (contenu JSON en base64) et adapter `mcp_servers/google_workspace/` pour le lire depuis l'environnement.

---

## 7. n8n sur Railway (optionnel)

Ajouter un service Docker dans le projet Railway :

```
Image : n8nio/n8n:latest
Port  : 5678
```

Variables d'environnement :
```bash
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=<mot-de-passe-fort>
N8N_HOST=<domaine-n8n>.up.railway.app
N8N_PORT=5678
N8N_PROTOCOL=https
WEBHOOK_URL=https://<domaine-n8n>.up.railway.app/
AGENTS_API_URL=https://dev-senior-api.up.railway.app
```

Mettre à jour les headers `X-API-Key` dans les workflows n8n importés.

---

## 8. CI/CD GitHub Actions

Deux workflows GitHub Actions sont disponibles :

| Workflow | Déclencheur | Action |
|---|---|---|
| `ci.yml` | Tout push/PR | Lint + types + tests + scan secrets |
| `docker.yml` | Push/PR/tag | Build image multi-arch (linux/amd64 + arm64) → push vers `ghcr.io` |
| `deploy.yml` | Push sur `main` | Déploiement sur le self-hosted runner Mac mini M4 (pull image + restart) |

Pour Railway/Vercel, le déploiement est déclenché automatiquement par push sur `main` via l'intégration GitHub de chaque plateforme. Le workflow `docker.yml` build et publie l'image sur ghcr.io — Railway/Vercel la récupèrent via le Dockerfile.

---

## 9. Checklist post-déploiement

- [ ] `GET /dev-senior/health` → `{"status": "ok"}`
- [ ] `GET /biz-manager/health` → `{"status": "ok"}`
- [ ] Frontend accessible sur l'URL Vercel
- [ ] Envoi d'un message dans le frontend → réponse streaming reçue
- [ ] Upload d'un fichier → texte extrait et pris en compte dans la réponse
- [ ] `DOCS_ENABLED=false` → Swagger inaccessible (`/docs` → 404)
- [ ] Qdrant indexé (`make index-codebase` depuis local)
- [ ] CORS configuré avec l'URL Vercel exacte

---

## 10. Variables d'environnement — récapitulatif complet

### Railway (API)

| Variable | Source | Obligatoire |
|---|---|---|
| `OPENROUTER_API_KEY` | OpenRouter | Oui |
| `AGENTS_API_KEY` | Générer | Oui |
| `DATABASE_URL` | Plugin PostgreSQL Railway | Oui |
| `REDIS_URL` | Plugin Redis Railway | Recommandé |
| `QDRANT_HOST` | Service Railway ou Qdrant Cloud | Oui |
| `QDRANT_PORT` | `6333` | Oui |
| `CORS_ORIGINS` | URL Vercel | Oui |
| `DOCS_ENABLED` | `false` | Oui (prod) |
| `LANGFUSE_PUBLIC_KEY` | Langfuse Cloud | Recommandé |
| `LANGFUSE_SECRET_KEY` | Langfuse Cloud | Recommandé |
| `GITHUB_TOKEN` | GitHub | Si MCP GitHub actif |
| `SLACK_SIGNING_SECRET` | Slack App | Si Slack actif |
| `TEAMS_WEBHOOK_KEY` | Teams Webhook | Si Teams actif |

### Vercel (Frontend)

| Variable | Valeur |
|---|---|
| `VITE_API_URL` | URL publique Railway |
| `VITE_API_KEY` | Même valeur que `AGENTS_API_KEY` |
| `VITE_BASE_PATH` | `/` |
