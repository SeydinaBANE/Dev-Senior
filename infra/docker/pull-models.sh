#!/bin/bash
# Télécharge les modèles dans le container Ollama
# Usage : ./pull-models.sh

set -e

OLLAMA_URL="http://localhost:11434"

wait_for_ollama() {
    echo "Attente du démarrage d'Ollama..."
    until curl -s "$OLLAMA_URL/api/tags" > /dev/null 2>&1; do
        sleep 2
    done
    echo "Ollama est prêt."
}

pull_model() {
    local model=$1
    echo "Téléchargement de $model..."
    docker exec ollama ollama pull "$model"
    echo "$model téléchargé."
}

wait_for_ollama

# Agent Dev Senior — modèle de code
pull_model "qwen2.5-coder:7b"

# Agent Business Manager — modèle généraliste
pull_model "llama3.1:8b"

# Embeddings — mémoire vectorielle (Phase 3)
pull_model "nomic-embed-text"

echo ""
echo "Modèles disponibles :"
docker exec ollama ollama list
