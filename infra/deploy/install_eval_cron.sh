#!/bin/bash
# Installe le cron d'évaluation automatique quotidienne (launchd, Mac mini M4)
# Usage : bash infra/deploy/install_eval_cron.sh
# À lancer UNE SEULE FOIS après le setup initial.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLIST_SRC="$PROJECT_DIR/infra/deploy/com.agents.eval.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.agents.eval.plist"
LOG_DIR="$PROJECT_DIR/logs"

echo "Installation du cron d'évaluation automatique..."

mkdir -p "$LOG_DIR"

sed "s|/path/to/project|$PROJECT_DIR|g" "$PLIST_SRC" > "$PLIST_DEST"

launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"

echo "Cron installé. Exécution quotidienne à 2h00."
echo "Logs disponibles dans : $LOG_DIR/eval.log"
echo ""
echo "Commandes utiles :"
echo "  launchctl list com.agents.eval          # vérifier le statut"
echo "  launchctl start com.agents.eval         # lancer manuellement"
echo "  tail -f $LOG_DIR/eval.log               # suivre les logs"
