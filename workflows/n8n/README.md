# Workflows n8n

5 workflows prêts à importer dans n8n.

## Import

1. Ouvrir n8n sur http://localhost:5678
2. Menu → **Workflows** → **Import from file**
3. Sélectionner le fichier JSON du workflow
4. Configurer les credentials manquants
5. Activer le workflow

## Variables d'environnement à configurer dans n8n

`Settings → Variables` :

| Variable | Description |
|---|---|
| `AGENTS_API_URL` | URL de l'API agents, ex: `http://host.docker.internal:8080` |
| `GITHUB_TOKEN` | Personal Access Token GitHub |
| `SENDER_EMAIL` | Email d'envoi |
| `REPORT_RECIPIENTS` | Emails destinataires du rapport SEO |
| `CONTENT_TEAM_EMAIL` | Email de l'équipe contenu |
| `SLACK_ALERT_CHANNEL` | Canal Slack pour les alertes (workflow 03) |

## Les 5 workflows

| # | Nom | Déclencheur | Agent | Description |
|---|---|---|---|---|
| 01 | PR Review Bot | Webhook GitHub | Dev Senior | Code review automatique à chaque nouvelle PR |
| 02 | Rapport SEO Hebdo | Cron lundi 8h | Biz Manager | Rapport Search Console + archivage Drive |
| 03 | Triage Email | Cron toutes les 30 min | Biz Manager | Classification et priorisation des emails |
| 04 | Onboarding Lead | Webhook CRM/formulaire | Biz Manager | Email de bienvenue + note CRM automatiques |
| 05 | Calendrier Contenu | Cron vendredi 10h | Biz Manager | Posts LinkedIn/Instagram de la semaine suivante |

## Credentials à configurer dans n8n

- **Google OAuth2** : pour Gmail, Drive (workflows 02, 03, 04, 05)
- **SMTP** : pour l'envoi d'emails (workflows 02, 05)
- **Slack** : optionnel, pour les alertes prioritaires (workflow 03)

## Démarrer l'API agents

L'API doit tourner pour que les workflows fonctionnent :

```bash
make api
```

L'API est disponible sur http://localhost:8080 (docs sur /docs).
