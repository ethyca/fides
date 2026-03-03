import pickle
import random
from base64 import b64encode
from datetime import datetime
from enum import Enum
from typing import Any, List
from unittest import mock

import pytest
from bson.objectid import ObjectId
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisClusterException
from redis.exceptions import TimeoutError as RedisTimeoutError

from fides.api.util.cache import (
    FidesopsRedis,
    cache_task_tracking_key,
    celery_tasks_in_flight,
)
from fides.api.util.custom_json_encoder import (
    ENCODED_BYTES_PREFIX,
    ENCODED_DATE_PREFIX,
    ENCODED_MONGO_OBJECT_ID_PREFIX,
)
from fides.config import CONFIG
from tests.fixtures.application_fixtures import faker


def test_get_cache(cache: FidesopsRedis) -> None:
    assert cache is not None
    assert callable(cache.set_with_autoexpire)


def test_cache_set_with_autoexpire(cache: FidesopsRedis) -> None:
    key = "a_key"
    value = "a_value"
    ttl_range = list(
        range(
            # Let's give this a 3 second buffer time to still pass
            CONFIG.redis.default_ttl_seconds - 2,
            CONFIG.redis.default_ttl_seconds + 1,
        )
    )
    cache.set_with_autoexpire(key, value)
    assert cache.ttl(key) in ttl_range
    assert cache.get(key) == value


def test_cache_set(cache: FidesopsRedis) -> None:
    key = "another_key"
    value = "another_value"
    res = cache.set(key, value)
    assert res


class CacheTestObject:
    def __init__(self, *values: Any):
        self.values = values

    def __eq__(self, other):
        return other.__hash__() == self.__hash__()

    def __hash__(self):
        return hash(self.values)


def test_encode_decode() -> None:
    for _ in range(10):
        test_obj = CacheTestObject(
            random.random(), random.randint(0, 1000), faker.name()
        )
        result = FidesopsRedis.decode_obj(FidesopsRedis.encode_obj(test_obj))
        assert CacheTestObject(*result["values"]) == test_obj


def test_decode_none():
    assert FidesopsRedis.decode_obj(None) is None


def test_scan(cache: FidesopsRedis) -> List:
    test_key = random.random()
    prefix = f"redis_key_{test_key}_"

    test_data = {
        f"{prefix}{i}": CacheTestObject(f"{prefix}{i}", random.random())
        for i in range(100)
    }
    for k, v in test_data.items():
        cache.set_encoded_object(k, v)

    keys = cache.get_keys_by_prefix(f"EN_{prefix}", random.randint(10, 100))
    assert len(keys) == 100

    cache.delete_keys_by_prefix(f"EN_{prefix}")
    keys = cache.get_keys_by_prefix(f"EN_{prefix}")
    assert len(keys) == 0


class TestCustomJSONEncoder:
    def test_encode_enum_string(self):
        class TestEnum(Enum):
            test = "test_value"

        result = FidesopsRedis.encode_obj({"key": TestEnum.test})

        assert result == '{"key": "test_value"}'

    def test_encode_enum_dict(self):
        class TestEnum(Enum):
            test = {"key": "test_value"}

        result = FidesopsRedis.encode_obj({"key": TestEnum.test})

        assert result == '{"key": {"key": "test_value"}}'

    def test_encode_object(self):
        class SomeClass:
            def __init__(self):
                self.val = "some value"

        assert FidesopsRedis.encode_obj(SomeClass()) == '{"val": "some value"}'

    @pytest.mark.parametrize(
        "value, expected",
        [
            (b"some value", f'"{ENCODED_BYTES_PREFIX}some%20value"'),
            (
                datetime(2023, 2, 14, 20, 58),
                f'"{ENCODED_DATE_PREFIX}{datetime(2023, 2, 14, 20, 58).isoformat()}"',
            ),
            (
                {"a": datetime(2023, 2, 14, 20, 58)},
                f'{{"a": "{ENCODED_DATE_PREFIX}{datetime(2023, 2, 14, 20, 58).isoformat()}"}}',
            ),
            (
                {"a": {"b": datetime(2023, 2, 14, 20, 58)}},
                f'{{"a": {{"b": "{ENCODED_DATE_PREFIX}{datetime(2023, 2, 14, 20, 58).isoformat()}"}}}}',
            ),
            ({"a": "b"}, '{"a": "b"}'),
            ({"a": {"b": "c"}}, '{"a": {"b": "c"}}'),
            (
                ObjectId("507f191e810c19729de860ea"),
                f'"{ENCODED_MONGO_OBJECT_ID_PREFIX}507f191e810c19729de860ea"',
            ),
            ({"a": 1}, '{"a": 1}'),
            ("some value", '"some value"'),
            (1, "1"),
        ],
    )
    def test_encode(self, value, expected):
        assert FidesopsRedis.encode_obj(value) == expected


class PickleObj:
    """For testing pickle decode."""

    def __init__(self):
        self.field = "value"


class TestCustomDecoder:
    @pytest.mark.parametrize(
        "value, expected",
        [
            (f'{{"a": "{ENCODED_BYTES_PREFIX}some%20value"}}', {"a": b"some value"}),
            (
                f'{{"a": "{ENCODED_MONGO_OBJECT_ID_PREFIX}507f191e810c19729de860ea"}}',
                {"a": ObjectId("507f191e810c19729de860ea")},
            ),
            (
                f'{{"a": "{ENCODED_DATE_PREFIX}{datetime(2023, 2, 17, 14, 5).isoformat()}"}}',
                {"a": datetime(2023, 2, 17, 14, 5)},
            ),
            (
                f'{{"a": {{"b": {{"c": "{ENCODED_DATE_PREFIX}{datetime(2023, 2, 17, 14, 5).isoformat()}"}}}}}}',
                {"a": {"b": {"c": datetime(2023, 2, 17, 14, 5)}}},
            ),
            (
                '{"birthday": "2001-11-08"}',
                {"birthday": "2001-11-08"},
            ),
            (
                '{"a": {"b": {"birthday": "2001-11-08"}}}',
                {"a": {"b": {"birthday": "2001-11-08"}}},
            ),
        ],
    )
    def test_cache_decode(self, value, expected):
        assert FidesopsRedis.decode_obj(value) == expected

    def test_decode_pickle_doesnt_break(self):
        """Test to ensure cache values in the old format don't break the decode."""
        value = b64encode(pickle.dumps(PickleObj()))
        assert FidesopsRedis.decode_obj(value) is None


class TestCacheTaskTrackingKey:
    def test_cache_tracking_key_privacy_request(self, privacy_request):
        assert privacy_request.get_cached_task_id() is None

        cache_task_tracking_key(privacy_request.id, "test_1234")

        assert privacy_request.get_cached_task_id() == "test_1234"

    def test_cache_tracking_key_request_task(self, request_task):
        """Request Task celery tasks are cached in the same location as Privacy Request"""
        assert request_task.get_cached_task_id() is None

        cache_task_tracking_key(request_task.id, "test_5678")

        assert request_task.get_cached_task_id() == "test_5678"


class TestCeleryTasksInFlight:
    def test_celery_tasks_in_flight_no_celery_tasks(self):
        assert not celery_tasks_in_flight([])

    @mock.patch("fides.api.util.cache.celery_app.control.inspect.query_task")
    def test_celery_tasks_in_flight_no_workers(self, query_task_mock):
        query_task_mock.return_value = {}

        assert not celery_tasks_in_flight(["1234"])

    @mock.patch("fides.api.util.cache.celery_app.control.inspect.query_task")
    def test_celery_tasks_in_flight_no_match_in_queue(self, query_task_mock):
        query_task_mock.return_value = {"@celery1234": {}}

        assert not celery_tasks_in_flight(["abcde"])

    @mock.patch("fides.api.util.cache.celery_app.control.inspect.query_task")
    def test_celery_tasks_in_flight_completed_state(self, query_task_mock):
        query_task_mock.return_value = {"@celery1234": {"abcde": ["completed", {}]}}

        assert not celery_tasks_in_flight(["abde"])

    @mock.patch("fides.api.util.cache.celery_app.control.inspect.query_task")
    def test_celery_tasks_in_flight_reserved_state(self, query_task_mock):
        query_task_mock.return_value = {"@celery1234": {"abcde": ["reserved", {}]}}

        assert celery_tasks_in_flight(["abde"])


def test_push_encoded_object_with_expiration(cache: FidesopsRedis) -> None:
    """Test that push_encoded_object correctly sets expiration time."""
    key = "test_list"
    test_obj = {"test": "value"}
    expire_time = 43200  # 12 hours in seconds

    # Push object and set expiration
    list_length = cache.push_encoded_object(key, test_obj, expire_time=expire_time)
    assert list_length == 1  # First item in list

    # Verify the item was stored correctly
    items = cache.get_decoded_list(key)
    assert len(items) == 1
    assert items[0] == test_obj

    # Verify expiration was set
    ttl = cache.ttl(key)
    assert (
        ttl <= expire_time and ttl > 0
    )  # TTL should be less than or equal to expire_time but greater than 0

    # Clean up
    cache.delete(key)


def test_push_encoded_object_default_expiration(cache: FidesopsRedis) -> None:
    """Test that push_encoded_object uses default TTL when no expiration is specified."""
    key = "test_list_default"
    test_obj = {"test": "value"}

    # Push object with default expiration
    list_length = cache.push_encoded_object(key, test_obj)
    assert list_length == 1

    # Verify expiration was set to default
    ttl = cache.ttl(key)
    assert ttl <= CONFIG.redis.default_ttl_seconds and ttl > 0

    # Clean up
    cache.delete(key)


class TestPrivacyRequestRetryCache:
    """Test the privacy request retry count cache functionality."""

    def test_get_privacy_request_retry_cache_key(self):
        """Test that retry cache key is generated correctly."""
        from fides.api.util.cache import get_privacy_request_retry_cache_key

        privacy_request_id = "test-privacy-request-123"
        expected_key = "id-test-privacy-request-123-privacy-request-retry-count"

        actual_key = get_privacy_request_retry_cache_key(privacy_request_id)
        assert actual_key == expected_key

    def test_get_privacy_request_retry_count_new_request(self, cache):
        """Test getting retry count for a new privacy request (should be 0)."""
        from fides.api.util.cache import get_privacy_request_retry_count

        privacy_request_id = "new-request-123"

        # Should return 0 for new request
        retry_count = get_privacy_request_retry_count(privacy_request_id)
        assert retry_count == 0

    def test_get_privacy_request_retry_count_existing(self, cache):
        """Test getting retry count for a privacy request with existing count."""
        from fides.api.util.cache import (
            get_privacy_request_retry_cache_key,
            get_privacy_request_retry_count,
        )

        privacy_request_id = "existing-request-456"
        expected_count = 3

        # Set up existing count in cache
        cache.set(
            get_privacy_request_retry_cache_key(privacy_request_id), expected_count
        )

        # Should return the existing count
        retry_count = get_privacy_request_retry_count(privacy_request_id)
        assert retry_count == expected_count

        # Clean up
        cache.delete(get_privacy_request_retry_cache_key(privacy_request_id))

    def test_get_privacy_request_retry_count_cache_failure(self, cache):
        """Test that cache failures in get_privacy_request_retry_count are raised."""
        from fides.api.util.cache import get_privacy_request_retry_count

        with mock.patch.object(cache, "get", side_effect=Exception("Cache error")):
            with pytest.raises(Exception) as exc_info:
                get_privacy_request_retry_count("test-request")
            assert "Cache error" in str(exc_info.value)

    def test_increment_privacy_request_retry_count_first_time(self, cache):
        """Test incrementing retry count for the first time."""
        from fides.api.util.cache import (
            get_privacy_request_retry_cache_key,
            increment_privacy_request_retry_count,
        )

        privacy_request_id = "first-increment-789"

        # First increment should return 1
        new_count = increment_privacy_request_retry_count(privacy_request_id)
        assert new_count == 1

        # Verify it's stored in cache
        cache_key = get_privacy_request_retry_cache_key(privacy_request_id)
        stored_count = cache.get(cache_key)
        assert int(stored_count) == 1

        # Verify expiration is set
        ttl = cache.ttl(cache_key)
        assert 0 < ttl <= 86400  # Should be set to 24 hours

        # Clean up
        cache.delete(cache_key)

    def test_increment_privacy_request_retry_count_multiple_times(self, cache):
        """Test incrementing retry count multiple times."""
        from fides.api.util.cache import (
            get_privacy_request_retry_cache_key,
            increment_privacy_request_retry_count,
        )

        privacy_request_id = "multi-increment-101112"
        cache_key = get_privacy_request_retry_cache_key(privacy_request_id)

        # Set initial count
        cache.set(cache_key, 2)

        # Increment should return 3
        new_count = increment_privacy_request_retry_count(privacy_request_id)
        assert new_count == 3

        # Increment again should return 4
        new_count = increment_privacy_request_retry_count(privacy_request_id)
        assert new_count == 4

        # Clean up
        cache.delete(cache_key)

    def test_increment_privacy_request_retry_count_cache_failure(self, cache):
        """Test that cache failures in increment_privacy_request_retry_count are raised."""
        from fides.api.util.cache import increment_privacy_request_retry_count

        with mock.patch.object(cache, "incr", side_effect=Exception("Cache error")):
            with pytest.raises(Exception) as exc_info:
                increment_privacy_request_retry_count("test-request")
            assert "Cache error" in str(exc_info.value)

    def test_reset_privacy_request_retry_count(self, cache):
        """Test resetting retry count."""
        from fides.api.util.cache import (
            get_privacy_request_retry_cache_key,
            get_privacy_request_retry_count,
            reset_privacy_request_retry_count,
        )

        privacy_request_id = "reset-test-131415"
        cache_key = get_privacy_request_retry_cache_key(privacy_request_id)

        # Set initial count
        cache.set(cache_key, 5)
        assert get_privacy_request_retry_count(privacy_request_id) == 5

        # Reset should remove the key
        reset_privacy_request_retry_count(privacy_request_id)

        # Count should now be 0 (key doesn't exist)
        assert get_privacy_request_retry_count(privacy_request_id) == 0

    def test_reset_privacy_request_retry_count_cache_failure(self, cache):
        """Test that cache failures in reset_privacy_request_retry_count are silently handled."""
        from fides.api.util.cache import reset_privacy_request_retry_count

        # This should not raise an exception even if cache fails
        with mock.patch.object(cache, "delete", side_effect=Exception("Cache error")):
            # Should complete without raising
            reset_privacy_request_retry_count("test-request")

    def test_retry_count_workflow_integration(self, cache):
        """Test the complete workflow of getting, incrementing, and resetting retry count."""
        from fides.api.util.cache import (
            get_privacy_request_retry_count,
            increment_privacy_request_retry_count,
            reset_privacy_request_retry_count,
        )

        privacy_request_id = "workflow-test-161718"

        # Start with 0
        assert get_privacy_request_retry_count(privacy_request_id) == 0

        # Increment several times
        assert increment_privacy_request_retry_count(privacy_request_id) == 1
        assert increment_privacy_request_retry_count(privacy_request_id) == 2
        assert increment_privacy_request_retry_count(privacy_request_id) == 3

        # Verify current count
        assert get_privacy_request_retry_count(privacy_request_id) == 3

        # Reset and verify
        reset_privacy_request_retry_count(privacy_request_id)
        assert get_privacy_request_retry_count(privacy_request_id) == 0


def _cluster_skip_reason(e: Exception) -> str:
    msg = str(e).lower()
    if "slots are not covered" in msg or "not covered after query" in msg:
        return (
            "Cluster slots not fully covered. Run cluster tests from inside Docker so "
            "the client can reach all nodes: docker compose run --rm fides env "
            "FIDES__REDIS__CLUSTER_ENABLED=true FIDES__REDIS__HOST=redis-cluster-node-1 "
            "FIDES__REDIS__PORT=6379 FIDES__REDIS__PASSWORD=redispassword "
            "uv run pytest tests/ops/util/test_cache.py::TestRedisClusterMode -v"
        )
    if "172.19.0" in msg or "connection refused" in msg:
        return (
            "Cluster nodes use Docker addresses. Run tests inside the stack: "
            "docker compose run --rm fides env FIDES__REDIS__CLUSTER_ENABLED=true "
            "FIDES__REDIS__HOST=redis-cluster-node-1 FIDES__REDIS__PORT=6379 "
            "FIDES__REDIS__PASSWORD=redispassword uv run pytest tests/ops/util/test_cache.py::TestRedisClusterMode -v"
        )
    return (
        "Redis cluster not reachable. Run tests inside Docker with HOST=redis-cluster-node-1 "
        "PORT=6379, or run without FIDES__REDIS__CLUSTER_ENABLED"
    )


@pytest.fixture
def redis_cluster_cache() -> FidesopsRedis:
    """
    Cache for TestRedisClusterMode. Skips when cluster is enabled but unreachable
    (e.g. CI without a running cluster) instead of failing with connection timeout.
    Run cluster tests from inside Docker: docker compose run --rm fides env
    FIDES__REDIS__CLUSTER_ENABLED=true FIDES__REDIS__HOST=redis-cluster-node-1
    FIDES__REDIS__PORT=6379 FIDES__REDIS__PASSWORD=redispassword
    uv run pytest tests/ops/util/test_cache.py::TestRedisClusterMode -v
    """
    from fides.api.util.cache import get_cache

    try:
        return get_cache()
    except (RedisClusterException, RedisConnectionError, RedisTimeoutError) as e:
        if CONFIG.redis.cluster_enabled:
            pytest.skip(f"{_cluster_skip_reason(e)}: {e}")
        raise


class TestRedisClusterMode:
    """
    Integration tests for Redis Cluster support in FidesopsRedis.
    Run against a real Redis (standalone or cluster) via redis_cluster_cache.
    With FIDES__REDIS__CLUSTER_ENABLED=true and a cluster, these exercise the
    cluster code paths (get_primaries scan, mget_nonatomic, delete_keys_by_prefix).
    Skips when cluster is enabled but unreachable.

    The Docker Compose cluster uses Docker hostnames so nodes can reach each other.
    Run these tests FROM INSIDE the stack so the client can reach all nodes:
      docker compose run --rm fides env \\
        FIDES__REDIS__CLUSTER_ENABLED=true FIDES__REDIS__HOST=redis-cluster-node-1 \\
        FIDES__REDIS__PORT=6379 FIDES__REDIS__PASSWORD=redispassword \\
        uv run pytest tests/ops/util/test_cache.py::TestRedisClusterMode -v
    """

    def test_fidesops_redis_wrapper_delegates_to_client(
        self, redis_cluster_cache: FidesopsRedis
    ):
        """Cache delegates get/set/ping to the underlying client."""
        key = f"cluster_test_{random.random()}_k"
        redis_cluster_cache.set(key, "v")
        assert redis_cluster_cache.get(key) == "v"
        assert redis_cluster_cache.ping() is True
        redis_cluster_cache.delete(key)

    def test_get_keys_by_prefix_uses_primaries_when_cluster(
        self, redis_cluster_cache: FidesopsRedis
    ):
        """get_keys_by_prefix returns all keys matching the prefix (cluster-aware)."""
        prefix = f"cluster_test_{random.random()}_id-1-identity-"
        redis_cluster_cache.set(f"{prefix}email", "e")
        redis_cluster_cache.set(f"{prefix}name", "n")
        keys = redis_cluster_cache.get_keys_by_prefix(prefix)
        assert len(keys) == 2
        assert f"{prefix}email" in keys
        assert f"{prefix}name" in keys
        redis_cluster_cache.delete(f"{prefix}email")
        redis_cluster_cache.delete(f"{prefix}name")

    def test_get_values_uses_mget_path(self, redis_cluster_cache: FidesopsRedis):
        """get_values returns a dict of key -> value (mget or mget_nonatomic)."""
        prefix = f"cluster_test_{random.random()}_"
        k1, k2 = f"{prefix}k1", f"{prefix}k2"
        redis_cluster_cache.set(k1, "v1")
        redis_cluster_cache.set(k2, "v2")
        result = redis_cluster_cache.get_values([k1, k2])
        assert result == {k1: "v1", k2: "v2"}
        redis_cluster_cache.delete(k1)
        redis_cluster_cache.delete(k2)

    def test_delete_keys_by_prefix_scans_then_deletes_when_cluster(
        self, redis_cluster_cache: FidesopsRedis
    ):
        """delete_keys_by_prefix removes all keys matching the prefix."""
        prefix = f"cluster_test_{random.random()}_p-"
        redis_cluster_cache.set(f"{prefix}a", "1")
        redis_cluster_cache.set(f"{prefix}b", "2")
        keys_before = redis_cluster_cache.get_keys_by_prefix(prefix)
        assert len(keys_before) == 2
        redis_cluster_cache.delete_keys_by_prefix(prefix)
        keys_after = redis_cluster_cache.get_keys_by_prefix(prefix)
        assert len(keys_after) == 0
