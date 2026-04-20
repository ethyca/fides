"""Unit tests for database pool health helpers (no integration DB required)."""

import asyncio
from unittest.mock import MagicMock

import pytest

from fides.api.v1.endpoints import health


class _FakeBindSqlite:
    dialect = type("Dialect", (), {"name": "sqlite"})()


class _FakeBindPostgresql:
    dialect = type("Dialect", (), {"name": "postgresql"})()


@pytest.mark.asyncio
async def test_check_async_session_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    """Slow execute should hit asyncio.wait_for and return unhealthy."""

    class _SlowSession:
        async def execute(self, *_args, **_kwargs) -> None:
            await asyncio.sleep(0.5)

        def get_bind(self) -> object:
            return _FakeBindSqlite()

    class _SlowCM:
        async def __aenter__(self) -> _SlowSession:
            return _SlowSession()

        async def __aexit__(self, *_args: object) -> None:
            return None

    monkeypatch.setattr(health, "DATABASE_HEALTHCHECK_QUERY_TIMEOUT_SECONDS", 0.15)

    def _factory() -> _SlowCM:
        return _SlowCM()

    result = await health._check_async_session(_factory)  # type: ignore[arg-type]
    assert result == "unhealthy"


@pytest.mark.asyncio
async def test_check_async_session_execute_error_returns_unhealthy() -> None:
    """Non-timeout errors from execute should return unhealthy."""

    class _ErrSession:
        async def execute(self, *_args, **_kwargs) -> None:
            raise RuntimeError("boom")

        def get_bind(self) -> object:
            return _FakeBindSqlite()

    class _ErrCM:
        async def __aenter__(self) -> _ErrSession:
            return _ErrSession()

        async def __aexit__(self, *_args: object) -> None:
            return None

    def _factory() -> _ErrCM:
        return _ErrCM()

    assert await health._check_async_session(_factory) == "unhealthy"  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_check_async_session_healthy_fast_path() -> None:
    """Fast session factory should return healthy."""

    class _FastSession:
        async def execute(self, *_args, **_kwargs) -> None:
            return None

        def get_bind(self) -> object:
            return _FakeBindSqlite()

    class _FastCM:
        async def __aenter__(self) -> _FastSession:
            return _FastSession()

        async def __aexit__(self, *_args: object) -> None:
            return None

    def _factory() -> _FastCM:
        return _FastCM()

    assert await health._check_async_session(_factory) == "healthy"  # type: ignore[arg-type]


def test_check_sync_session_postgresql_sets_statement_timeout() -> None:
    """PostgreSQL binds should run SET LOCAL before SELECT 1."""
    db = MagicMock()
    db.get_bind.return_value = _FakeBindPostgresql()

    assert health._check_sync_session(db) == "healthy"
    assert db.execute.call_count == 2
    first_sql = str(db.execute.call_args_list[0][0][0])
    assert "SET LOCAL statement_timeout" in first_sql
    assert "SELECT 1" in str(db.execute.call_args_list[1][0][0])


def test_check_sync_session_non_postgresql_single_execute() -> None:
    """Non-PostgreSQL dialects should only run SELECT 1."""
    db = MagicMock()
    db.get_bind.return_value = _FakeBindSqlite()

    assert health._check_sync_session(db) == "healthy"
    assert db.execute.call_count == 1
    assert "SELECT 1" in str(db.execute.call_args_list[0][0][0])


def test_check_sync_session_execute_error_returns_unhealthy() -> None:
    db = MagicMock()
    db.get_bind.return_value = _FakeBindSqlite()
    db.execute.side_effect = RuntimeError("connection refused")

    assert health._check_sync_session(db) == "unhealthy"


def test_bind_dialect_name_async_engine_shape() -> None:
    """AsyncEngine exposes dialect via sync_engine."""

    class _FakeAsyncBind:
        sync_engine = type(
            "SE", (), {"dialect": type("D", (), {"name": "postgresql"})()}
        )()

    assert health._bind_dialect_name(_FakeAsyncBind()) == "postgresql"
