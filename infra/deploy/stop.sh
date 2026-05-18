#!/bin/bash
# Arrêt propre de tous les services
# Usage : bash infra/deploy/stop.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"

log() { echo "[stop] $1"; }

# ── API agents ────────────────────────────────────────────────────────────────
PLIST="$HOME/Library/LaunchAgents/com.agents.api.plist"
if [[ -f "$PLIST" ]]; then
    launchctl unload "$PLIST" 2>/dev/null && log "API arrêtée (launchd)." || true
elif [[ -f "$LOG_DIR/api.pid" ]]; then
    PID=$(cat "$LOG_DIR/api.pid")
    kill "$PID" 2>/dev/null && log "API arrêtée (PID $PID)." || true
    rm -f "$LOG_DIR/api.pid"
fi

# ── Docker ────────────────────────────────────────────────────────────────────
log "Arrêt des containers Docker..."
docker compose -f "$PROJECT_DIR/infra/docker/docker-compose.yml" down
log "Containers arrêtés."
