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

check "Ollama"    "http://localhost:11434/api/tags"        "models"  || ERRORS=$((ERRORS+1))
check "ChromaDB"  "http://localhost:8000/api/v1/heartbeat" "nanosecond_heartbeat" || ERRORS=$((ERRORS+1))
check "API agents" "http://localhost:8080/health"          "ok"      || ERRORS=$((ERRORS+1))
check "n8n"       "http://localhost:5678/healthz"          ""        || ERRORS=$((ERRORS+1))

# Vérifier les modèles Ollama
echo ""
echo "--- Modèles Ollama ---"
for model in "qwen2.5-coder:7b" "llama3.1:8b" "nomic-embed-text"; do
    if docker exec ollama ollama list 2>/dev/null | grep -q "$model"; then
        echo -e "$OK $model"
    else
        echo -e "$FAIL $model manquant — lancer : make models"
        ERRORS=$((ERRORS+1))
    fi
done

echo ""
if [[ $ERRORS -eq 0 ]]; then
    echo "Tout est opérationnel."
else
    echo "$ERRORS service(s) en erreur."
    exit 1
fi
