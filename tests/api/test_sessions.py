"""Tests for SessionStore — RedisSessionStore and PostgresSessionStore."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.sessions import RedisSessionStore, PostgresSessionStore, SessionStore


# ── RedisSessionStore ─────────────────────────────────────────────────────────

@pytest.fixture
def redis_client() -> MagicMock:
    client = MagicMock()
    client.ping = AsyncMock()
    client.hset = AsyncMock()
    client.hget = AsyncMock(return_value=json.dumps([]))
    client.expire = AsyncMock()
    client.delete = AsyncMock()
    client.aclose = AsyncMock()
    return client


@pytest.fixture
def redis_store(redis_client: MagicMock) -> RedisSessionStore:
    return RedisSessionStore(redis_client)


@pytest.mark.asyncio
async def test_redis_new_session(redis_store: RedisSessionStore, redis_client: MagicMock) -> None:
    session_id = await redis_store.new_session("dev-senior")
    assert len(session_id) == 36  # UUID format
    redis_client.hset.assert_awaited_once()
    redis_client.expire.assert_awaited_once()


@pytest.mark.asyncio
async def test_redis_get_history_empty(redis_store: RedisSessionStore, redis_client: MagicMock) -> None:
    redis_client.hget.return_value = json.dumps([])
    history = await redis_store.get_history("some-id")
    assert history == []


@pytest.mark.asyncio
async def test_redis_get_history_missing_key(redis_store: RedisSessionStore, redis_client: MagicMock) -> None:
    redis_client.hget.return_value = None
    history = await redis_store.get_history("missing-id")
    assert history == []
    redis_client.expire.assert_not_awaited()


@pytest.mark.asyncio
async def test_redis_get_history_refreshes_ttl(redis_store: RedisSessionStore, redis_client: MagicMock) -> None:
    redis_client.hget.return_value = json.dumps([{"role": "user"}])
    await redis_store.get_history("some-id")
    redis_client.expire.assert_awaited_once()


@pytest.mark.asyncio
async def test_redis_set_history(redis_store: RedisSessionStore, redis_client: MagicMock) -> None:
    history = [{"role": "user", "content": "hello"}]
    await redis_store.set_history("some-id", history)
    redis_client.hset.assert_awaited_once()
    redis_client.expire.assert_awaited_once()


@pytest.mark.asyncio
async def test_redis_delete_session(redis_store: RedisSessionStore, redis_client: MagicMock) -> None:
    await redis_store.delete_session("some-id")
    redis_client.delete.assert_awaited_once_with("session:some-id")


@pytest.mark.asyncio
async def test_redis_close(redis_store: RedisSessionStore, redis_client: MagicMock) -> None:
    await redis_store.close()
    redis_client.aclose.assert_awaited_once()


def test_redis_backend_property(redis_store: RedisSessionStore) -> None:
    assert redis_store.backend == "redis"


# ── PostgresSessionStore ──────────────────────────────────────────────────────

@pytest.fixture
def pg_pool() -> MagicMock:
    pool = MagicMock()
    pool.execute = AsyncMock()
    pool.fetchrow = AsyncMock(return_value=None)
    pool.close = AsyncMock()
    return pool


@pytest.fixture
def pg_store(pg_pool: MagicMock) -> PostgresSessionStore:
    return PostgresSessionStore(pg_pool)


@pytest.mark.asyncio
async def test_postgres_new_session(pg_store: PostgresSessionStore, pg_pool: MagicMock) -> None:
    session_id = await pg_store.new_session("biz-manager")
    assert len(session_id) == 36
    pg_pool.execute.assert_awaited_once()
    call_sql = pg_pool.execute.call_args[0][0]
    assert "INSERT INTO sessions" in call_sql


@pytest.mark.asyncio
async def test_postgres_get_history_missing(pg_store: PostgresSessionStore, pg_pool: MagicMock) -> None:
    pg_pool.fetchrow.return_value = None
    pg_pool.execute = AsyncMock()  # _cleanup_expired call
    history = await pg_store.get_history("missing-id")
    assert history == []


@pytest.mark.asyncio
async def test_postgres_get_history_existing(pg_store: PostgresSessionStore, pg_pool: MagicMock) -> None:
    payload = [{"role": "user", "content": "test"}]
    pg_pool.fetchrow.return_value = {"history": json.dumps(payload)}
    history = await pg_store.get_history("some-id")
    assert history == payload


@pytest.mark.asyncio
async def test_postgres_set_history(pg_store: PostgresSessionStore, pg_pool: MagicMock) -> None:
    history = [{"role": "assistant", "content": "hi"}]
    await pg_store.set_history("some-id", history)
    pg_pool.execute.assert_awaited_once()
    call_sql = pg_pool.execute.call_args[0][0]
    assert "UPDATE sessions" in call_sql


@pytest.mark.asyncio
async def test_postgres_delete_session(pg_store: PostgresSessionStore, pg_pool: MagicMock) -> None:
    await pg_store.delete_session("some-id")
    pg_pool.execute.assert_awaited_once_with("DELETE FROM sessions WHERE id = $1", "some-id")


@pytest.mark.asyncio
async def test_postgres_close(pg_store: PostgresSessionStore, pg_pool: MagicMock) -> None:
    await pg_store.close()
    pg_pool.close.assert_awaited_once()


def test_postgres_backend_property(pg_store: PostgresSessionStore) -> None:
    assert pg_store.backend == "postgres"


# ── SessionStore.create() factory ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_factory_selects_redis_when_url_set() -> None:
    mock_store = MagicMock(spec=RedisSessionStore)
    with patch.dict("os.environ", {"REDIS_URL": "redis://localhost:6379/0"}):
        with patch(
            "api.sessions.RedisSessionStore.from_url",
            new=AsyncMock(return_value=mock_store),
        ):
            store = await SessionStore.create()
    assert store is mock_store


@pytest.mark.asyncio
async def test_factory_selects_postgres_when_no_redis() -> None:
    mock_store = MagicMock(spec=PostgresSessionStore)
    with patch.dict("os.environ", {}, clear=False):
        # ensure REDIS_URL is absent
        import os
        os.environ.pop("REDIS_URL", None)
        with patch(
            "api.sessions.PostgresSessionStore.create",
            new=AsyncMock(return_value=mock_store),
        ):
            store = await SessionStore.create()
    assert store is mock_store
