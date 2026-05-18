# Guide — Agent Business Manager

**Pour les business managers et stagiaires — aucune compétence technique requise**

---

## C'est quoi ?

Le Business Manager est ton assistant IA personnel pour le marketing, le contenu, le SEO et les tâches business du quotidien. Tu lui parles en français, il fait le reste.

---

## Comment l'utiliser

### Option 1 — En ligne de commande (pour les habitués du terminal)

```bash
make biz-manager
```

### Option 2 — Via l'interface web n8n (recommandé pour les non-tech)

1. Ouvre http://localhost:5678
2. Connexion : `admin` / `changeme` (ou les credentials fournis)
3. Les workflows sont déjà prêts — active ceux dont tu as besoin

### Option 3 — Via l'API (pour les intégrations)

Envoie une requête POST à `http://localhost:8080/biz-manager/task` avec ton message.

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

## Bonnes pratiques

**Donne du contexte.** Plus tu précises le contexte (audience, objectif, ton), meilleure est la réponse.

```
❌ "Écris un post LinkedIn"
✓  "Écris un post LinkedIn de 150 mots sur notre offre SEO,
    pour une audience de dirigeants de PME, ton expert mais humain,
    avec un appel à l'action vers notre formulaire de contact"
```

**Demande des variantes.** Tu peux toujours demander une version différente.

```
Toi > Donne-moi 3 versions différentes, de plus en plus directes
```

**L'agent se souvient.** Dans la même session, il se souvient de ce que tu as dit. Tu peux affiner sans tout ré-expliquer.

```
Toi > [après avoir demandé un email] Raccourcis-le et mets le CTA en premier
```

---

## En cas de problème

**L'agent ne répond plus**
→ Attends 30 secondes (charge du modèle) ou appelle l'équipe technique.

**La réponse n'est pas satisfaisante**
→ Reformule en ajoutant plus de contexte, ou demande "Peux-tu reformuler en étant plus [direct / créatif / formel] ?"

**Les workflows n8n ne se déclenchent pas**
→ Vérifier sur http://localhost:5678 que le workflow est bien en statut **Active**.

**Contact équipe technique** : [à compléter selon l'organisation]
