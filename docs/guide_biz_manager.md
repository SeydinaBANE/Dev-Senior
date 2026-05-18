# Guide — Agent Business Manager

**Pour les business managers et stagiaires — aucune compétence technique requise**

---

## C'est quoi ?

Le Business Manager est ton assistant IA personnel pour le marketing, le contenu, le SEO et les tâches business du quotidien. Tu lui parles en français, il fait le reste.

Il partage aussi sa mémoire avec l'agent Dev Senior : les informations importantes que tu lui communiques peuvent enrichir automatiquement le contexte de l'équipe technique.

---

## Comment l'utiliser

### Option 1 — Interface web (recommandé)

1. Ouvre **http://localhost:5173** (ou http://localhost:8080/app en prod)
2. Sélectionne **Business Manager** dans la barre latérale
3. Tape ton message et appuie sur Entrée

### Option 2 — Slack (accès depuis le chat d'équipe)

Dans n'importe quel canal Slack où le bot est présent :
```
/biz-manager Rédige 3 posts LinkedIn sur notre nouvelle offre SEO
```
→ La réponse arrive dans le canal en quelques secondes.

### Option 3 — Microsoft Teams

Mentionne le bot dans un canal Teams :
```
@biz-manager Analyse ce lead et propose un email de suivi
```

### Option 4 — Via l'interface n8n (workflows automatiques)

1. Ouvre http://localhost:5678
2. Connexion : `admin` / le mot de passe fourni par l'équipe technique
3. Les workflows sont déjà prêts — active ceux dont tu as besoin

### Option 5 — En ligne de commande (pour les habitués du terminal)

```bash
make biz-manager
```

---

## Exemples concrets

### Créer du contenu

```
Toi > Rédige 3 posts LinkedIn sur le thème "productivité avec l'IA"
      pour une audience de PME françaises. Ton professionnel mais accessible.
```

```
Toi > Écris une newsletter de 400 mots sur nos nouveautés du mois.
      Inclus un appel à l'action vers notre page de contact.
```

### SEO

```
Toi > Analyse le mot-clé "agent IA entreprise" et donne-moi 10 idées d'articles de blog
```

```
Toi > Réécris ce titre de page pour qu'il soit mieux optimisé SEO :
      "Nos services de conseil en transformation digitale"
```

### Emails et communication

```
Toi > Rédige un email de relance pour un prospect qui n'a pas répondu depuis 2 semaines.
      Ton : chaleureux, sans pression, avec une valeur ajoutée.
```

```
Toi > Prépare un email d'annonce pour le lancement de notre nouveau service.
      Destinataires : notre base clients existants.
```

### Google Workspace (via MCP)

```
Toi > Montre-moi les 10 derniers fichiers modifiés sur mon Drive
Toi > Crée un Google Doc "Stratégie Q3 2026" avec ce contenu : [...]
Toi > Quels sont mes événements de la semaine prochaine ?
Toi > Crée un rendez-vous "Réunion équipe" mardi 20 mai à 14h pour 1h
```

### CRM HubSpot

```
Toi > Cherche le contact jean.dupont@example.com
Toi > Liste les opportunités commerciales en cours
Toi > Ajoute une note sur le contact 12345 : "Intéressé par l'offre Premium"
```

### Rapports automatiques

Les rapports suivants sont **entièrement automatiques** via n8n :
- **Rapport SEO** : chaque lundi 8h dans ta boîte mail
- **Calendrier contenu** : chaque vendredi 10h avec les posts de la semaine
- **Triage email** : toutes les 30 min, les emails prioritaires sont signalés

---

## Workflows automatisés (n8n)

Pour activer un workflow :
1. Aller sur http://localhost:5678
2. Cliquer sur le workflow
3. Cliquer sur le bouton **Active** (en haut à droite)

| Workflow | Ce qu'il fait | Fréquence |
|---|---|---|
| PR Review Bot | Commente automatiquement les nouvelles PRs GitHub | À chaque PR |
| Rapport SEO Hebdo | Envoie un rapport SEO par email | Lundi 8h |
| Triage Email | Classe et priorise les emails entrants | Toutes les 30 min |
| Onboarding Lead | Envoie un email de bienvenue aux nouveaux prospects | Dès qu'un lead arrive |
| Calendrier Contenu | Génère les posts de la semaine | Vendredi 10h |

---

## Dashboard métriques

L'équipe technique peut consulter l'onglet **Dashboard** de l'interface web pour voir la santé des agents :
- Temps de réponse moyen
- Taux d'erreur
- Score de qualité des réponses (mis à jour chaque nuit automatiquement)

---

## Bonnes pratiques

**Donne du contexte.** Plus tu précises le contexte (audience, objectif, ton), meilleure est la réponse.

```
❌ "Écris un post LinkedIn"
✓  "Écris un post LinkedIn de 150 mots sur notre offre SEO,
    pour une audience de dirigeants de PME, ton expert mais humain,
    avec un appel à l'action vers notre formulaire de contact"
```

**Demande des variantes.**

```
Toi > Donne-moi 3 versions différentes, de plus en plus directes
```

**L'agent se souvient.** Dans la même session, il se souvient de ce que tu as dit. Tu peux affiner sans tout ré-expliquer.

```
Toi > [après avoir demandé un email] Raccourcis-le et mets le CTA en premier
```

---

## En cas de problème

**L'interface web ne s'ouvre pas**
→ Contacter l'équipe technique pour qu'elle lance `make api` et `make frontend`.

**Le slash command Slack ne répond pas**
→ Vérifier auprès de l'équipe technique que `SLACK_SIGNING_SECRET` est configuré et que la Slack App est active.

**Le bot Teams ne répond pas**
→ Vérifier que le webhook sortant Teams est actif et que `TEAMS_WEBHOOK_KEY` est configuré.

**L'agent ne répond plus**
→ Attends 30 secondes. Si ça persiste, appelle l'équipe technique.

**La réponse n'est pas satisfaisante**
→ Reformule en ajoutant plus de contexte, ou demande "Peux-tu reformuler en étant plus [direct / créatif / formel] ?"

**Les workflows n8n ne se déclenchent pas**
→ Vérifier sur http://localhost:5678 que le workflow est bien en statut **Active**.

**Contact équipe technique** : [à compléter selon l'organisation]
