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
