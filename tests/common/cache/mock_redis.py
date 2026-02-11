"""
Shared MockRedis implementation for DSR cache store tests.
"""

import fnmatch
from typing import Dict, List, Optional, Set, Union

RedisValue = Union[bytes, float, int, str]


class MockRedis:
    """Mock Redis with minimal interface for DSRCacheStore."""

    def __init__(self) -> None:
        self._data: Dict[str, RedisValue] = {}
        self._sets: Dict[str, Set[Union[str, bytes]]] = {}

    def get(self, key: str) -> Optional[Union[str, bytes]]:
        val = self._data.get(key)
        return val if isinstance(val, (str, bytes)) else str(val) if val else None

    def set(self, key: str, value: RedisValue, ex: Optional[int] = None) -> bool:
        self._data[key] = value
        return True

    def delete(self, *keys: str) -> int:
        deleted = sum(1 for k in keys if self._data.pop(k, None) or self._sets.pop(k, None))
        return deleted

    def keys(self, pattern: str) -> List[str]:
        return [k for k in self._data if fnmatch.fnmatch(k, pattern)]

    def scan_iter(self, match: str = "*", count: Optional[int] = None):
        return iter(self.keys(match))

    def sadd(self, key: str, *members: Union[str, bytes]) -> int:
        s = self._sets.setdefault(key, set())
        before = len(s)
        s.update(members)
        return len(s) - before

    def srem(self, key: str, *members: Union[str, bytes]) -> int:
        if key not in self._sets:
            return 0
        before = len(self._sets[key])
        self._sets[key].difference_update(members)
        return before - len(self._sets[key])

    def smembers(self, key: str) -> Set[Union[str, bytes]]:
        return self._sets.get(key, set()).copy()
