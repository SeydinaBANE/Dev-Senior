"""
Pool de connexions asyncpg pour PostgreSQL.
Initialisé dans le lifespan de FastAPI.
"""
import os
import asyncpg
from fastapi import Request

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://agents:change-this-password@localhost:5432/agents_db",
)


async def create_pool() -> asyncpg.Pool:
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id          TEXT PRIMARY KEY,
                agent       TEXT NOT NULL,
                history     TEXT NOT NULL DEFAULT '[]',
                created_at  TIMESTAMPTZ DEFAULT NOW(),
                updated_at  TIMESTAMPTZ DEFAULT NOW()
            )
        """)
    return pool


def get_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.pool
