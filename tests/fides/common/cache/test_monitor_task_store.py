import pytest

from fides.common.cache.monitor_task_store import MonitorTaskCacheStore


@pytest.mark.unit
class TestMonitorTaskCacheStore:
    @pytest.fixture
    def store(self, mock_redis) -> MonitorTaskCacheStore:
        return MonitorTaskCacheStore(mock_redis)

    def test_set_and_check_stopped(self, store):
        """set_stopped sets a flag that is_stopped can read."""
        assert store.is_stopped("celery-123") is False

        store.set_stopped("celery-123")

        assert store.is_stopped("celery-123") is True

    def test_is_stopped_different_celery_id(self, store):
        """Stopping one task doesn't affect others."""
        store.set_stopped("celery-aaa")

        assert store.is_stopped("celery-aaa") is True
        assert store.is_stopped("celery-bbb") is False

    def test_set_stopped_raises_on_redis_failure(self, mock_redis):
        """set_stopped raises if Redis is unavailable."""
        mock_redis.set.side_effect = ConnectionError("Redis down")
        store = MonitorTaskCacheStore(mock_redis)

        with pytest.raises(ConnectionError):
            store.set_stopped("celery-123")

    def test_is_stopped_returns_false_on_redis_failure(self, mock_redis):
        """is_stopped returns False if Redis is unavailable."""
        mock_redis.get.side_effect = ConnectionError("Redis down")
        store = MonitorTaskCacheStore(mock_redis)

        assert store.is_stopped("celery-123") is False
