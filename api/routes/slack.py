"""
Intégration Slack — slash commands /dev-senior et /biz-manager.

Configuration Slack App :
  1. Créer une Slack App sur https://api.slack.com/apps
  2. Activer "Slash Commands" → créer /dev-senior et /biz-manager
     Request URL : https://<ton-domaine>/slack/command
  3. Copier le Signing Secret dans SLACK_SIGNING_SECRET
  4. (optionnel) Token Bot pour les réponses enrichies : SLACK_BOT_TOKEN

Fonctionnement :
  - Slack envoie un POST form-encoded dans les 3 secondes
  - On vérifie la signature HMAC-SHA256, on renvoie un ack immédiat
  - Un BackgroundTask appelle l'agent et poste le résultat via response_url
  - La mémoire de conversation est persistée par canal+utilisateur (session_key = slack:{channel_id}:{user_id})
  - Envoyer "reset" réinitialise la mémoire du canal pour cet utilisateur
"""
import hashlib
import hmac
import os
import time
from typing import TYPE_CHECKING, Annotated
from urllib.parse import parse_qs

import httpx
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status
from pydantic_ai.messages import ModelMessagesTypeAdapter

from agents.dev_senior.agent import agent as dev_agent
from agents.biz_manager.agent import agent as biz_agent

if TYPE_CHECKING:
    from api.sessions import SessionStore

router = APIRouter(prefix="/slack", tags=["Slack"])

_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")
_MAX_TIMESTAMP_DRIFT = 300  # 5 minutes


def _verify_signature(
    body: bytes,
    timestamp: str,
    signature: str,
) -> None:
    """Lève 403 si la signature Slack est invalide ou trop vieille."""
    if not _SIGNING_SECRET:
        return  # désactivé en dev si clé absente

    try:
        ts = int(timestamp)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Timestamp invalide")

    if abs(time.time() - ts) > _MAX_TIMESTAMP_DRIFT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Timestamp expiré")

    base = f"v0:{timestamp}:{body.decode()}"
    expected = "v0=" + hmac.new(
        _SIGNING_SECRET.encode(), base.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, signature or ""):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Signature invalide")


async def _run_agent_and_reply(
    agent_name: str,
    text: str,
    response_url: str,
    sessions: "SessionStore",
    session_key: str,
) -> None:
    """Appelé en background : run l'agent avec historique et poste la réponse à Slack."""
    agent = dev_agent if agent_name == "dev-senior" else biz_agent
    history_raw = await sessions.get_history(session_key)
    history = ModelMessagesTypeAdapter.validate_python(history_raw) if history_raw else []
    try:
        result = await agent.run(text, message_history=history)
        reply = result.data
        messages = ModelMessagesTypeAdapter.dump_python(result.all_messages(), mode="json")
        await sessions.set_history(session_key, messages)
    except Exception as exc:
        reply = f":warning: Erreur agent `{agent_name}` : {exc}"

    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            response_url,
            json={"response_type": "in_channel", "text": reply},
        )


@router.post("/command")
async def slack_command(
    request: Request,
    background_tasks: BackgroundTasks,
    x_slack_request_timestamp: Annotated[str | None, Header()] = None,
    x_slack_signature: Annotated[str | None, Header()] = None,
) -> dict:
    """Reçoit un slash command Slack et répond en différé via response_url."""
    # Lire le body brut AVANT tout parsing pour que la vérification HMAC soit possible
    body = await request.body()
    _verify_signature(body, x_slack_request_timestamp or "", x_slack_signature or "")

    # Parser le form-encoded body manuellement
    fields = parse_qs(body.decode(), keep_blank_values=True)
    command = fields.get("command", [""])[0]
    text = fields.get("text", [""])[0].strip()
    response_url = fields.get("response_url", [""])[0]
    user_name = fields.get("user_name", [""])[0]
    channel_id = fields.get("channel_id", ["unknown"])[0]
    user_id = fields.get("user_id", ["unknown"])[0]
    session_key = f"slack:{channel_id}:{user_id}"

    if not text:
        return {"response_type": "ephemeral", "text": "Usage : `/dev-senior <message>`"}

    agent_name = "dev-senior" if command == "/dev-senior" else "biz-manager"
    sessions = request.app.state.sessions

    if text.lower() == "reset":
        await sessions.delete_session(session_key)
        return {"response_type": "ephemeral", "text": ":recycle: Mémoire de la conversation réinitialisée."}

    # Ack immédiat pour respecter le délai 3s de Slack
    background_tasks.add_task(
        _run_agent_and_reply, agent_name, text, response_url, sessions, session_key
    )

    return {
        "response_type": "in_channel",
        "text": f":hourglass: `{user_name}` → _{text}_ — réponse en cours…",
    }


@router.get("/health")
async def health() -> dict:
    configured = bool(_SIGNING_SECRET)
    return {"status": "ok", "slack_configured": configured}
