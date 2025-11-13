from unittest.mock import MagicMock, patch

import pytest

from fides.api.util.lock import get_redis_lock, redis_lock


class TestRedisLock:
    def test_redis_lock_acquired(self, loguru_caplog):
        """
        Tests that the redis_lock context manager yields the lock when acquired.
        """
        lock_key = "test_lock_acquired"
        with redis_lock(lock_key, 10) as lock:
            assert lock is not None
            assert lock.owned()
            assert f"Acquired lock for '{lock_key}'." in loguru_caplog.text

        assert not lock.owned()
        assert f"Released lock for '{lock_key}'." in loguru_caplog.text

    def test_redis_lock_not_acquired(self, loguru_caplog):
        """
        Tests that the redis_lock context manager yields None when the lock is not acquired.
        """
        lock_key = "test_lock_not_acquired"
        # Acquire the lock beforehand to simulate another process holding the lock
        external_lock = get_redis_lock(lock_key, 10)
        assert external_lock.acquire(blocking=False)

        try:
            with redis_lock(lock_key, 10) as lock:
                assert lock is None
                assert (
                    f"Another process is already running for lock '{lock_key}'. Skipping this execution."
                    in loguru_caplog.text
                )
        finally:
            # Release the external lock to clean up
            external_lock.release()

    @pytest.mark.parametrize(
        "blocking,blocking_timeout,expected_blocking,expected_timeout",
        [
            # blocking=True with no timeout - should use lock timeout as blocking timeout
            (True, 0, True, 10),
            # blocking=True with explicit timeout - should use explicit timeout
            (True, 60, True, 60),
            # blocking=False (default) - should use default values
            (False, 0, False, 0),
        ],
    )
    @patch("fides.api.util.lock.get_redis_lock")
    def test_redis_lock_blocking_parameters(
        self,
        mock_get_redis_lock,
        blocking,
        blocking_timeout,
        expected_blocking,
        expected_timeout,
    ):
        """
        Tests that redis_lock correctly passes blocking and blocking_timeout parameters to lock.acquire.
        """
        mock_lock = MagicMock()
        mock_lock.acquire.return_value = True
        mock_lock.owned.return_value = True
        mock_get_redis_lock.return_value = mock_lock

        lock_timeout = 10
        with redis_lock(
            "test_key",
            lock_timeout,
            blocking=blocking,
            blocking_timeout=blocking_timeout,
        ) as lock:
            assert lock is not None

        # Verify acquire was called with correct blocking parameters
        mock_lock.acquire.assert_called_once_with(
            blocking=expected_blocking, blocking_timeout=expected_timeout
        )
        mock_lock.release.assert_called_once()
