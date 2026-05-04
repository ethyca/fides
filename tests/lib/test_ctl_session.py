from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import create_async_engine

from fides.api.db.ctl_session import warm_async_pool
from fides.config import CONFIG


class TestWarmAsyncPool:
    async def test_opens_and_closes_all_connections(self) -> None:
        """All connections are opened concurrently and then closed."""
        pool_size = 5
        mock_conns = [AsyncMock() for _ in range(pool_size)]
        engine = AsyncMock()
        engine.connect = AsyncMock(side_effect=mock_conns)

        await warm_async_pool("test-pool", pool_size, engine)

        assert engine.connect.call_count == pool_size
        for conn in mock_conns:
            conn.close.assert_awaited_once()

    async def test_partial_failure_closes_successful_connections(self) -> None:
        """If some connections fail, the successful ones are still closed."""
        good_conn_1 = AsyncMock()
        good_conn_2 = AsyncMock()
        engine = AsyncMock()
        engine.connect = AsyncMock(
            side_effect=[good_conn_1, ConnectionError("refused"), good_conn_2]
        )

        await warm_async_pool("test-pool", 3, engine)

        assert engine.connect.call_count == 3
        good_conn_1.close.assert_awaited_once()
        good_conn_2.close.assert_awaited_once()

    async def test_all_connections_fail(self) -> None:
        """If every connection fails, no close calls are made and no exception propagates."""
        engine = AsyncMock()
        engine.connect = AsyncMock(side_effect=ConnectionError("refused"))

        await warm_async_pool("test-pool", 3, engine)

        assert engine.connect.call_count == 3

    async def test_warms_real_engine(self) -> None:
        """Warming a real async engine fills the connection pool."""
        pool_size = 3
        engine = create_async_engine(
            CONFIG.database.async_database_uri, pool_size=pool_size, max_overflow=0
        )
        try:
            await warm_async_pool("test-pool", pool_size, engine)
            assert engine.pool.checkedin() == pool_size
        finally:
            await engine.dispose()
