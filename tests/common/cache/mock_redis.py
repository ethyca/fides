"""
Shared in-memory Redis mock for cache tests.

Provides MockPipeline and MockRedis with pipeline(), ttl(), expire(), scan_iter(),
and the operations needed by RedisCacheManager and DSRCacheStore.
"""

import fnmatch
from typing import Any, Iterator, List, Optional, Set, Union


class MockPipeline:
    """In-memory pipeline that batches commands and executes atomically."""

    def __init__(self, data: dict, sets: dict) -> None:
        self._data = data
        self._sets = sets
        self._commands: list = []

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> "MockPipeline":
        self._commands.append(("set", (key, value, ex)))
        return self

    def sadd(self, key: str, member: str) -> "MockPipeline":
        self._commands.append(("sadd", (key, member)))
        return self

    def delete(self, *keys: str) -> "MockPipeline":
        self._commands.append(("delete", keys))
        return self

    def srem(self, key: str, member: str) -> "MockPipeline":
        self._commands.append(("srem", (key, member)))
        return self

    def execute(self) -> list:
        results = []
        for op, args in self._commands:
            if op == "set":
                key, value, _ = args
                self._data[key] = value
                results.append(True)
            elif op == "sadd":
                key, member = args
                if key not in self._sets:
                    self._sets[key] = set()
                self._sets[key].add(member)
                results.append(1)
            elif op == "delete":
                for k in args:
                    self._data.pop(k, None)
                    self._sets.pop(k, None)
                results.append(len(args))
            elif op == "srem":
                key, member = args
                if key in self._sets:
                    self._sets[key].discard(member)
                    if not self._sets[key]:
                        del self._sets[key]
                results.append(1)
        self._commands = []
        return results


class MockRedis:
    """In-memory Redis mock for RedisCacheManager and DSRCacheStore tests."""

    def __init__(self) -> None:
        self._data: dict = {}
        self._sets: dict = {}
        self._ttl: dict = {}  # key -> seconds until expiry (simplified; no decay)

    def get(self, key: str) -> Optional[Any]:
        return self._data.get(key)

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        self._data[key] = value
        return True

    def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if k in self._data:
                del self._data[k]
                count += 1
            if k in self._sets:
                del self._sets[k]
                count += 1
            self._ttl.pop(k, None)
        return count

    def sadd(self, key: str, member: str) -> int:
        if key not in self._sets:
            self._sets[key] = set()
        self._sets[key].add(member)
        return 1

    def srem(self, key: str, member: str) -> int:
        if key in self._sets:
            self._sets[key].discard(member)
            if not self._sets[key]:
                del self._sets[key]
            return 1
        return 0

    def smembers(self, key: str) -> Set[Union[str, bytes]]:
        return self._sets.get(key, set()).copy()

    def keys(self, pattern: str = "*") -> List[str]:
        all_keys = set(self._data) | set(self._sets)
        return [k for k in all_keys if fnmatch.fnmatch(k, pattern)]

    def scan_iter(self, match: str = "*", count: Optional[int] = None) -> Iterator[str]:
        """Iterate over keys matching the pattern (used by DSRCacheStore.clear)."""
        yield from self.keys(match)

    def ttl(self, key: str) -> int:
        if key not in self._data and key not in self._sets:
            return -2
        return self._ttl.get(key, -1)

    def expire(self, key: str, seconds: int) -> bool:
        if key in self._data or key in self._sets:
            self._ttl[key] = seconds
            return True
        return False

    def pipeline(self) -> MockPipeline:
        return MockPipeline(self._data, self._sets)
