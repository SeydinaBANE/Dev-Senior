"""
Endpoint de métriques — agrège les stats runtime et les scores qualité.

GET /metrics  → requiert X-API-Key (sauf si AGENTS_API_KEY absent)
"""

import json
from pathlib import Path

from fastapi import APIRouter, Depends

from api.auth import require_api_key
from api.metrics_store import get_all_metrics

router = APIRouter(prefix="/metrics", tags=["Métriques"])

RESULTS_DIR = Path("observability/evals/results")
AGENTS = ["dev-senior", "biz-manager"]


def _latest_eval_scores() -> dict[str, dict]:
    """Charge les scores du dernier fichier d'éval pour chaque agent."""
    scores: dict[str, dict] = {}
    for agent in AGENTS:
        files = sorted(RESULTS_DIR.glob(f"{agent}_*.json"), reverse=True)
        if not files:
            continue
        try:
            samples = json.loads(files[0].read_text())
            if not samples:
                continue
            fields = ["score", "helpfulness", "accuracy", "safety"]
            scores[agent] = {
                f: round(sum(s[f] for s in samples) / len(samples), 2)
                for f in fields
                if all(f in s for s in samples)
            }
        except Exception:
            continue
    return scores


@router.get("", dependencies=[Depends(require_api_key)])
async def metrics() -> dict:
    """Retourne les métriques runtime (latence, erreurs) et les scores qualité."""
    return {
        "agents": get_all_metrics(),
        "eval": _latest_eval_scores(),
    }
