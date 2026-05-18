"""
Gestion des sessions de conversation.

Backend sélectionné automatiquement selon l'environnement :
  - REDIS_URL défini → RedisSessionStore  (TTL natif, O(1) read/write)
  - sinon            → PostgresSessionStore (comportement historique)

Usage :
    store = await SessionStore.create()          # dans le lifespan FastAPI
    session_id = await store.new_session(agent)
    history    = await store.get_history(session_id)
    await store.set_history(session_id, history)
    await store.delete_session(session_id)
    await store.close()
"""
import json
import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta

import asyncpg

SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "3600"))  # 60 min


class SessionStore(ABC):
    """Interface commune aux deux backends."""

    @classmethod
    async def create(cls) -> "SessionStore":
        redis_url = os.getenv("REDIS_URL", "")
        if redis_url:
            return await RedisSessionStore.from_url(redis_url)
        return await PostgresSessionStore.create()

    @abstractmethod
    async def new_session(self, agent: str) -> str: ...

    @abstractmethod
    async def get_history(self, session_id: str) -> list: ...

    @abstractmethod
    async def set_history(self, session_id: str, history: list) -> None: ...

    @abstractmethod
    async def delete_session(self, session_id: str) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...

    @property
    @abstractmethod
    def backend(self) -> str: ...


# ── Backend Redis ─────────────────────────────────────────────────────────────

class RedisSessionStore(SessionStore):
    def __init__(self, client: "redis.asyncio.Redis") -> None:  # type: ignore[name-defined]
        self._client = client

    @classmethod
    async def from_url(cls, url: str) -> "RedisSessionStore":
        import redis.asyncio as aioredis
        client = aioredis.from_url(url, decode_responses=True)
        await client.ping()
        return cls(client)

    async def new_session(self, agent: str) -> str:
        session_id = str(uuid.uuid4())
        key = f"session:{session_id}"
        await self._client.hset(key, mapping={"agent": agent, "history": "[]"})
        await self._client.expire(key, SESSION_TTL_SECONDS)
        return session_id

    async def get_history(self, session_id: str) -> list:
        key = f"session:{session_id}"
        data = await self._client.hget(key, "history")
        if data is None:
            return []
        await self._client.expire(key, SESSION_TTL_SECONDS)
        return json.loads(data)

    async def set_history(self, session_id: str, history: list) -> None:
        key = f"session:{session_id}"
        await self._client.hset(key, "history", json.dumps(history))
        await self._client.expire(key, SESSION_TTL_SECONDS)

    async def delete_session(self, session_id: str) -> None:
        await self._client.delete(f"session:{session_id}")

    async def close(self) -> None:
        await self._client.aclose()

    @property
    def backend(self) -> str:
        return "redis"


# ── Backend PostgreSQL ────────────────────────────────────────────────────────

class PostgresSessionStore(SessionStore):
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @classmethod
    async def create(cls) -> "PostgresSessionStore":
        from api.db import create_pool
        pool = await create_pool()
        return cls(pool)

    async def new_session(self, agent: str) -> str:
        session_id = str(uuid.uuid4())
        await self._pool.execute(
            "INSERT INTO sessions (id, agent, history) VALUES ($1, $2, $3)",
            session_id, agent, "[]",
        )
        return session_id

    async def get_history(self, session_id: str) -> list:
        await self._cleanup_expired()
        row = await self._pool.fetchrow(
            "SELECT history FROM sessions WHERE id = $1", session_id
        )
        if not row:
            return []
        await self._pool.execute(
            "UPDATE sessions SET updated_at = $1 WHERE id = $2",
            datetime.now(timezone.utc), session_id,
        )
        return json.loads(row["history"])

    async def set_history(self, session_id: str, history: list) -> None:
        await self._pool.execute(
            "UPDATE sessions SET history = $1, updated_at = $2 WHERE id = $3",
            json.dumps(history), datetime.now(timezone.utc), session_id,
        )

    async def delete_session(self, session_id: str) -> None:
        await self._pool.execute("DELETE FROM sessions WHERE id = $1", session_id)

    async def close(self) -> None:
        await self._pool.close()

    async def _cleanup_expired(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=SESSION_TTL_SECONDS)
        await self._pool.execute("DELETE FROM sessions WHERE updated_at < $1", cutoff)

    @property
    def backend(self) -> str:
        return "postgres"
