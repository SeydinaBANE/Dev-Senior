#!/bin/bash
# Démarre tout l'environnement agents sur Mac mini M4
# Usage : bash infra/deploy/start.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV="$PROJECT_DIR/.venv"
LOG_DIR="$PROJECT_DIR/logs"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[start]${NC} $1"; }
warn() { echo -e "${YELLOW}[warn]${NC}  $1"; }
fail() { echo -e "${RED}[fail]${NC}  $1"; exit 1; }

mkdir -p "$LOG_DIR"

# ── 1. Docker (Qdrant + PostgreSQL + n8n) ─────────────────────────────────────
log "Démarrage des containers Docker..."
docker compose -f "$PROJECT_DIR/infra/docker/docker-compose.yml" up -d

# ── 2. Attendre Qdrant ────────────────────────────────────────────────────────
log "Attente de Qdrant..."
TRIES=0
until curl -sf http://localhost:6333/healthz > /dev/null 2>&1; do
    sleep 2
    TRIES=$((TRIES + 1))
    [[ $TRIES -ge 20 ]] && fail "Qdrant ne répond pas après 40s"
done
log "Qdrant prêt."

# ── 3. Attendre PostgreSQL ────────────────────────────────────────────────────
log "Attente de PostgreSQL..."
TRIES=0
until docker exec postgres pg_isready -U "${POSTGRES_USER:-agents}" -d "${POSTGRES_DB:-agents_db}" > /dev/null 2>&1; do
    sleep 2
    TRIES=$((TRIES + 1))
    [[ $TRIES -ge 20 ]] && fail "PostgreSQL ne répond pas après 40s"
done
log "PostgreSQL prêt."

# ── 4. API agents ─────────────────────────────────────────────────────────────
log "Démarrage de l'API agents..."
PLIST="$HOME/Library/LaunchAgents/com.agents.api.plist"
if [[ -f "$PLIST" ]]; then
    launchctl unload "$PLIST" 2>/dev/null || true
    launchctl load "$PLIST"
    log "API démarrée via launchd."
else
    warn "Plist launchd introuvable. Démarrage manuel..."
    nohup "$VENV/bin/uvicorn" api.main:app \
        --host 0.0.0.0 --port 8080 \
        --log-level info \
        > "$LOG_DIR/api.log" 2>&1 &
    echo $! > "$LOG_DIR/api.pid"
    log "API démarrée (PID: $(cat "$LOG_DIR/api.pid"))."
fi

# ── 5. Health check final ─────────────────────────────────────────────────────
sleep 4
bash "$PROJECT_DIR/infra/deploy/healthcheck.sh"
