#!/bin/bash
# Arrêt propre de tous les services
# Usage : bash infra/deploy/stop.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

log() { echo "[stop] $1"; }

log "Arrêt de tous les containers Docker..."
docker compose -f "$PROJECT_DIR/infra/docker/docker-compose.yml" down
log "Tous les services arrêtés."
