"""
Gestion des sessions de conversation pour l'API HTTP.

Stocke l'historique en mémoire (dict) avec TTL.
Pour une vraie prod : remplacer par Redis.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

SESSION_TTL_MINUTES = 60

_sessions: dict[str, dict[str, Any]] = {}


def new_session() -> str:
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {"history": [], "updated_at": datetime.now(timezone.utc)}
    return session_id


def get_history(session_id: str) -> list:
    _cleanup_expired()
    session = _sessions.get(session_id)
    if not session:
        return []
    session["updated_at"] = datetime.now(timezone.utc)
    return session["history"]


def set_history(session_id: str, history: list) -> None:
    if session_id not in _sessions:
        _sessions[session_id] = {}
    _sessions[session_id]["history"] = history
    _sessions[session_id]["updated_at"] = datetime.now(timezone.utc)


def delete_session(session_id: str) -> None:
    _sessions.pop(session_id, None)


def _cleanup_expired() -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=SESSION_TTL_MINUTES)
    expired = [sid for sid, s in _sessions.items() if s.get("updated_at", cutoff) < cutoff]
    for sid in expired:
        del _sessions[sid]
