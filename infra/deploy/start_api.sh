#!/bin/bash
# Wrapper launchd : charge .env puis démarre uvicorn.
# Ce script est référencé par com.agents.api.plist.
# Le plist ne peut pas sourcer un fichier — ce wrapper fait le pont.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="$PROJECT_DIR/.env"

# Charger les variables d'environnement depuis .env
if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
fi

mkdir -p "$PROJECT_DIR/logs"

exec "$PROJECT_DIR/.venv/bin/uvicorn" api.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8080}" \
    --workers 2 \
    --log-level info
