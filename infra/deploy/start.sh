#!/bin/bash
# Démarre tout l'environnement agents sur Mac mini M4
# Usage : bash infra/deploy/start.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[start]${NC} $1"; }
warn() { echo -e "${YELLOW}[warn]${NC}  $1"; }
fail() { echo -e "${RED}[fail]${NC}  $1"; exit 1; }

log "Chargement de .env..."
if [[ -f "$PROJECT_DIR/.env" ]]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

log "Démarrage de tous les services (infra + agents-api)..."
docker compose -f "$PROJECT_DIR/infra/docker/docker-compose.yml" up -d

log "Attente de Qdrant..."
TRIES=0
until curl -sf http://localhost:6333/healthz > /dev/null 2>&1; do
    sleep 2
    TRIES=$((TRIES + 1))
    [[ $TRIES -ge 20 ]] && fail "Qdrant ne répond pas après 40s"
done
log "Qdrant prêt."

log "Attente de PostgreSQL..."
TRIES=0
until docker exec postgres pg_isready -U "${POSTGRES_USER:-agents}" -d "${POSTGRES_DB:-agents_db}" > /dev/null 2>&1; do
    sleep 2
    TRIES=$((TRIES + 1))
    [[ $TRIES -ge 20 ]] && fail "PostgreSQL ne répond pas après 40s"
done
log "PostgreSQL prêt."

if docker ps --format '{{.Names}}' | grep -q "^redis$"; then
    log "Attente de Redis..."
    TRIES=0
    until docker exec redis redis-cli ping > /dev/null 2>&1; do
        sleep 2
        TRIES=$((TRIES + 1))
        [[ $TRIES -ge 15 ]] && fail "Redis ne répond pas après 30s"
    done
    log "Redis prêt."
fi

log "Attente de l'API agents..."
TRIES=0
until curl -sf http://localhost:"${PORT:-8080}"/dev-senior/health > /dev/null 2>&1; do
    sleep 3
    TRIES=$((TRIES + 1))
    [[ $TRIES -ge 15 ]] && fail "API agents ne répond pas après 45s"
done
log "API agents prête."

bash "$PROJECT_DIR/infra/deploy/healthcheck.sh"
