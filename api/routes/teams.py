"""
Intégration Microsoft Teams — outgoing webhook.

Configuration Teams :
  1. Dans Teams : Paramètres de l'équipe → Applications → Créer un webhook sortant
     Callback URL : https://<ton-domaine>/teams/message
  2. Copier le token HMAC dans TEAMS_WEBHOOK_KEY
  3. Mentionner le bot dans un canal : "@DevSenior <message>" ou "@BizManager <message>"

Routage :
  - Message commence par "@devsénior", "@dev-senior", "@devsênior" → agent Dev Senior
  - Message commence par "@bizmanager", "@biz-manager"             → agent Biz Manager
  - Sinon → agent Dev Senior par défaut

Mémoire :
  - La conversation est persistée par Teams conversation ID (session_key = teams:{conversation_id})
  - Envoyer "reset" réinitialise la mémoire de la conversation
"""
import base64
import hashlib
import hmac
import os
import re

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from pydantic_ai.messages import ModelMessagesTypeAdapter

from agents.dev_senior.agent import agent as dev_agent
from agents.biz_manager.agent import agent as biz_agent

router = APIRouter(prefix="/teams", tags=["Teams"])

_WEBHOOK_KEY = os.getenv("TEAMS_WEBHOOK_KEY", "")

# Noms de mention acceptés pour chaque agent
_DEV_PATTERNS = re.compile(r"^@dev[- ]?s[eé]nior\b", re.IGNORECASE)
_BIZ_PATTERNS = re.compile(r"^@biz[- ]?manager\b", re.IGNORECASE)


class TeamsMessage(BaseModel):
    type: str = ""
    text: str = ""
    conversation: dict[str, str] = {}


def _verify_signature(body: bytes, authorization: str | None) -> None:
    """Lève 403 si le HMAC Teams est invalide."""
    if not _WEBHOOK_KEY:
        return  # désactivé en dev si clé absente

    if not authorization or not authorization.startswith("HMAC "):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Header Authorization manquant")

    key_bytes = base64.b64decode(_WEBHOOK_KEY)
    expected = base64.b64encode(
        hmac.new(key_bytes, body, hashlib.sha256).digest()
    ).decode()

    provided = authorization[5:]  # strip "HMAC "
    if not hmac.compare_digest(expected, provided):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Signature HMAC invalide")


def _parse_agent_and_text(raw: str) -> tuple[str, str]:
    """Retourne (agent_name, cleaned_text) depuis le message Teams brut."""
    # Teams encode le texte en HTML léger — on retire les balises
    text = re.sub(r"<[^>]+>", " ", raw).strip()
    text = re.sub(r"\s+", " ", text)

    if _BIZ_PATTERNS.match(text):
        cleaned = _BIZ_PATTERNS.sub("", text).strip()
        return "biz-manager", cleaned or text
    # Dev Senior par défaut (mention ou non)
    cleaned = _DEV_PATTERNS.sub("", text).strip()
    return "dev-senior", cleaned or text


@router.post("/message")
async def teams_message(request: Request, msg: TeamsMessage) -> dict:
    """Reçoit un message Teams et retourne la réponse de l'agent."""
    body = await request.body()
    auth_header = request.headers.get("authorization")
    _verify_signature(body, auth_header)

    if not msg.text.strip():
        return {"type": "message", "text": "Message vide — rien à traiter."}

    agent_name, text = _parse_agent_and_text(msg.text)
    agent = dev_agent if agent_name == "dev-senior" else biz_agent

    conversation_id = msg.conversation.get("id", "unknown")
    session_key = f"teams:{conversation_id}"
    sessions = request.app.state.sessions

    if text.lower() == "reset":
        await sessions.delete_session(session_key)
        return {"type": "message", "text": "Mémoire de la conversation réinitialisée."}

    history_raw = await sessions.get_history(session_key)
    history = ModelMessagesTypeAdapter.validate_python(history_raw) if history_raw else []

    try:
        result = await agent.run(text, message_history=history)
        reply = result.data
        messages = ModelMessagesTypeAdapter.dump_python(result.all_messages(), mode="json")
        await sessions.set_history(session_key, messages)
    except Exception as exc:
        reply = f"Erreur agent `{agent_name}` : {exc}"

    return {"type": "message", "text": reply}


@router.get("/health")
async def health() -> dict:
    configured = bool(_WEBHOOK_KEY)
    return {"status": "ok", "teams_configured": configured}
