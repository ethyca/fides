import pickle
import random
from base64 import b64encode
from datetime import datetime, timezone
from enum import Enum
from typing import Any, List

from fides.api.ops.util.cache import FidesopsRedis
from fides.core.config import CONFIG
import pytest
from bson.objectid import ObjectId

from fides.api.ops.util.cache import (
    ENCODED_BYTES_PREFIX,
    ENCODED_MONGO_OBJECT_ID_PREFIX,
    FidesopsRedis,
)

from ..fixtures.application_fixtures import faker


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

        cache = FidesopsRedis()
        result = cache.encode_obj({"key": TestEnum.test})

        assert result == '{"key": "test_value"}'

    def test_encode_enum_dict(self):
        class TestEnum(Enum):
            test = {"key": "test_value"}

        cache = FidesopsRedis()
        result = cache.encode_obj({"key": TestEnum.test})

        assert result == '{"key": {"key": "test_value"}}'

    def test_encode_object(self):
        class SomeClass:
            def __init__(self):
                self.val = "some value"

        cache = FidesopsRedis()
        assert cache.encode_obj(SomeClass()) == '{"val": "some value"}'

    @pytest.mark.parametrize(
        "value, expected",
        [
            (b"some value", f'"{ENCODED_BYTES_PREFIX}some%20value"'),
            (
                datetime(2023, 2, 14, 20, 58),
                f'"{datetime(2023, 2, 14, 20, 58).isoformat()}"',
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
        cache = FidesopsRedis()
        assert cache.encode_obj(value) == expected


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
                f'{{"a": "{datetime(2023, 2, 17, 14, 5).isoformat()}"}}',
                {"a": datetime(2023, 2, 17, 14, 5)},
            ),
            (
                f'{{"a": "{ENCODED_MONGO_OBJECT_ID_PREFIX}507f191e810c19729de860ea"}}',
                {"a": ObjectId("507f191e810c19729de860ea")},
            ),
        ],
    )
    def test_decode_bytes(self, value, expected):
        cache = FidesopsRedis()
        assert cache.decode_obj(value) == expected

    def test_decode_pickle_doesnt_break(self):
        """Test to ensure cache values in the old format don't break the decode."""
        value = b64encode(pickle.dumps(PickleObj()))
        cache = FidesopsRedis()
        assert cache.decode_obj(value) is None
