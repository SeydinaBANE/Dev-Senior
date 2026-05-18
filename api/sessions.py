"""
Gestion des sessions de conversation — stockage PostgreSQL (asyncpg).
"""
import uuid
import json
from datetime import datetime, timezone, timedelta

import asyncpg

SESSION_TTL_MINUTES = 60


async def new_session(pool: asyncpg.Pool, agent: str) -> str:
    session_id = str(uuid.uuid4())
    await pool.execute(
        "INSERT INTO sessions (id, agent, history) VALUES ($1, $2, $3)",
        session_id,
        agent,
        "[]",
    )
    return session_id


async def get_history(pool: asyncpg.Pool, session_id: str) -> list:
    await _cleanup_expired(pool)
    row = await pool.fetchrow("SELECT history FROM sessions WHERE id = $1", session_id)
    if not row:
        return []
    await pool.execute(
        "UPDATE sessions SET updated_at = $1 WHERE id = $2",
        datetime.now(timezone.utc),
        session_id,
    )
    return json.loads(row["history"])


async def set_history(pool: asyncpg.Pool, session_id: str, history: list) -> None:
    await pool.execute(
        "UPDATE sessions SET history = $1, updated_at = $2 WHERE id = $3",
        json.dumps(history),
        datetime.now(timezone.utc),
        session_id,
    )


async def delete_session(pool: asyncpg.Pool, session_id: str) -> None:
    await pool.execute("DELETE FROM sessions WHERE id = $1", session_id)


async def _cleanup_expired(pool: asyncpg.Pool) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=SESSION_TTL_MINUTES)
    await pool.execute("DELETE FROM sessions WHERE updated_at < $1", cutoff)
