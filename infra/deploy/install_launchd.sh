#!/bin/bash
# Installe le service launchd pour l'API agents (Mac mini M4)
# Usage : bash infra/deploy/install_launchd.sh
# À lancer UNE SEULE FOIS après le setup initial.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLIST_SRC="$PROJECT_DIR/infra/deploy/com.agents.api.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.agents.api.plist"
LOG_DIR="$PROJECT_DIR/logs"

echo "Installation du service launchd..."

# Créer le dossier de logs
mkdir -p "$LOG_DIR"

# Vérifier que .env existe
if [[ ! -f "$PROJECT_DIR/.env" ]]; then
    echo "ERREUR : $PROJECT_DIR/.env introuvable."
    echo "Copier .env.example → .env et remplir les variables avant d'installer le service."
    exit 1
fi

# Remplacer /path/to/project par le vrai chemin (plist + wrapper)
sed "s|/path/to/project|$PROJECT_DIR|g" "$PLIST_SRC" > "$PLIST_DEST"

# Rendre le wrapper exécutable
chmod +x "$PROJECT_DIR/infra/deploy/start_api.sh"

# Charger le service
launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"

echo "Service installé et démarré."
echo "Logs disponibles dans : $LOG_DIR/api.log"
echo ""
echo "Commandes utiles :"
echo "  launchctl list com.agents.api          # vérifier le statut"
echo "  launchctl stop com.agents.api          # arrêter"
echo "  launchctl start com.agents.api         # démarrer"
echo "  tail -f $LOG_DIR/api.log               # suivre les logs"
