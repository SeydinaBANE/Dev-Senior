"""
Authentification par clé API pour l'API agents.

Comportement :
- Si AGENTS_API_KEY est défini dans .env → clé requise sur tous les endpoints
- Si non défini → accès libre (mode dev local uniquement)

Utilisation dans une route :
    from fastapi import Depends
    from api.auth import require_api_key

    @router.post("/chat", dependencies=[Depends(require_api_key)])
"""

import os

from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str | None = Security(_api_key_header)) -> None:
    expected = os.getenv("AGENTS_API_KEY", "").strip()
    if not expected:
        # Pas de clé configurée = mode dev (accès libre)
        # En prod, AGENTS_API_KEY doit impérativement être défini
        return
    if not api_key or api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clé API invalide ou manquante (header X-API-Key requis)",
        )
