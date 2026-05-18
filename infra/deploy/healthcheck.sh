#!/bin/bash
# Vérifie que tous les services répondent
# Usage : bash infra/deploy/healthcheck.sh
# Retourne 0 si tout est OK, 1 sinon

set -euo pipefail

OK='\033[0;32m✓\033[0m'
FAIL='\033[0;31m✗\033[0m'

check() {
    local name="$1"
    local url="$2"
    local expected="${3:-}"

    if response=$(curl -sf --max-time 5 "$url" 2>/dev/null); then
        if [[ -n "$expected" ]] && ! echo "$response" | grep -q "$expected"; then
            echo -e "$FAIL $name ($url) — réponse inattendue"
            return 1
        fi
        echo -e "$OK $name"
        return 0
    else
        echo -e "$FAIL $name ($url) — non joignable"
        return 1
    fi
}

echo ""
echo "=== Health Check — $(date '+%Y-%m-%d %H:%M:%S') ==="
echo ""

ERRORS=0

check "Qdrant"      "http://localhost:6333/healthz"      ""    || ERRORS=$((ERRORS+1))
check "PostgreSQL"  "http://localhost:8080/health"       "ok"  || ERRORS=$((ERRORS+1))
check "API agents"  "http://localhost:8080/health"       "ok"  || ERRORS=$((ERRORS+1))
check "n8n"         "http://localhost:5678/healthz"      ""    || ERRORS=$((ERRORS+1))

# Vérifier PostgreSQL directement si psql est disponible
echo ""
echo "--- PostgreSQL ---"
if command -v psql &>/dev/null; then
    if PGPASSWORD="${POSTGRES_PASSWORD:-change-this-password}" psql \
        -h localhost -U "${POSTGRES_USER:-agents}" -d "${POSTGRES_DB:-agents_db}" \
        -c "SELECT 1" &>/dev/null 2>&1; then
        echo -e "$OK PostgreSQL (connexion directe OK)"
    else
        echo -e "$FAIL PostgreSQL (connexion directe KO)"
        ERRORS=$((ERRORS+1))
    fi
else
    echo "(psql non disponible — vérification via API uniquement)"
fi

echo ""
if [[ $ERRORS -eq 0 ]]; then
    echo "Tout est opérationnel."
else
    echo "$ERRORS service(s) en erreur."
    exit 1
fi
