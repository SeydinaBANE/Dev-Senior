# Workflows n8n

5 workflows prêts à importer dans n8n.

## Import

1. Ouvrir n8n sur http://localhost:5678
2. Menu → **Workflows** → **Import from file**
3. Sélectionner le fichier JSON
4. Configurer les credentials manquants
5. Activer le workflow

## Variables à configurer dans n8n

`Settings → Variables` :

| Variable | Description | Obligatoire |
|---|---|---|
| `AGENTS_API_URL` | URL de l'API agents — `http://host.docker.internal:8080` | ✅ |
| `AGENTS_API_KEY` | Clé API (valeur de `AGENTS_API_KEY` dans `.env`) | ✅ |
| `GITHUB_TOKEN` | Personal Access Token GitHub (scopes : `repo`) | Workflow 01 |
| `SENDER_EMAIL` | Email d'envoi | Workflows 02, 04, 05 |
| `REPORT_RECIPIENTS` | Email(s) destinataires rapport SEO | Workflow 02 |
| `CONTENT_TEAM_EMAIL` | Email équipe contenu | Workflow 05 |
| `SLACK_ALERT_CHANNEL` | Canal Slack alertes (ex: `#alertes`) | Workflow 03 |

## Les 5 workflows

| # | Nom | Déclencheur | Agent |
|---|---|---|---|
| 01 | PR Review Bot | Webhook GitHub (nouvelle PR) | Dev Senior |
| 02 | Rapport SEO Hebdo | Cron lundi 8h | Biz Manager |
| 03 | Triage Email | Cron toutes les 30 min | Biz Manager |
| 04 | Onboarding Lead | Webhook CRM/formulaire | Biz Manager |
| 05 | Calendrier Contenu | Cron vendredi 10h | Biz Manager |

## Credentials à configurer dans n8n

`Settings → Credentials` :
- **Google OAuth2** : pour Gmail, Drive (workflows 02, 03, 04, 05)
- **SMTP** : pour l'envoi d'emails (workflows 02, 05)
- **Slack** : optionnel, alertes prioritaires (workflow 03)

## Démarrer l'API agents

```bash
make api    # port 8080, Swagger sur http://localhost:8080/docs
```

Tous les appels depuis n8n vers l'API incluent le header `X-API-Key: {{ $env.AGENTS_API_KEY }}`.
