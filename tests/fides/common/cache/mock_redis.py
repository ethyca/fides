"""
Autospec'd Redis mock with in-memory backing store for cache tests.

Uses ``create_autospec(redis.Redis)`` so that:
- Method signatures are validated against the real Redis client
- Missing methods surface as clear errors, not silent misbehavior
- New Redis methods used in production code are auto-available
"""

import fnmatch
from typing import Any
from unittest.mock import MagicMock, create_autospec

import redis as redis_lib

__all__ = ["create_mock_redis"]


def create_mock_redis() -> MagicMock:
    """
    Create an autospec'd ``redis.Redis`` mock with in-memory state.

    The mock validates method signatures against real ``redis.Redis``,
    while providing stateful in-memory behavior via side_effects.

    Internal state is accessible for test assertions::

        mock._data  -- dict of string keys to values
        mock._sets  -- dict of set keys to set[str]
        mock._ttls  -- dict of keys to TTL seconds
    """
    mock = create_autospec(redis_lib.Redis, instance=True)

    _data: dict[str, Any] = {}
    _sets: dict[str, set[str]] = {}
    _ttls: dict[str, int] = {}

    # Expose state for test assertions
    mock._data = _data
    mock._sets = _sets
    mock._ttls = _ttls

    # --- Core Redis methods ---

    def _get(name):
        return _data.get(name)

    def _set(name, value, ex=None, **kwargs):
        _data[name] = value
        if ex is not None:
            _ttls[name] = ex
        return True

    def _setex(name, time, value):
        _data[name] = value
        _ttls[name] = time
        return True

    def _delete(*names):
        count = 0
        for n in names:
            if n in _data:
                del _data[n]
                count += 1
            if n in _sets:
                del _sets[n]
                count += 1
            _ttls.pop(n, None)
        return count

    def _exists(*names):
        return sum(1 for n in names if n in _data or n in _sets)

    def _sadd(name, *values):
        _sets.setdefault(name, set()).update(values)
        return len(values)

    def _srem(name, *values):
        if name in _sets:
            for v in values:
                _sets[name].discard(v)
            if not _sets[name]:
                del _sets[name]
        return len(values)

    def _smembers(name):
        return _sets.get(name, set()).copy()

    def _keys(pattern="*"):
        all_keys = set(_data) | set(_sets)
        return [k for k in all_keys if fnmatch.fnmatch(k, pattern)]

    def _scan_iter(match="*", count=None, **kwargs):
        return iter(_keys(match))

    def _ttl_fn(name):
        if name not in _data and name not in _sets:
            return -2
        return _ttls.get(name, -1)

    def _expire(name, time):
        if name in _data or name in _sets:
            _ttls[name] = time
            return True
        return False

    def _ping(**kwargs):
        return True

    mock.get.side_effect = _get
    mock.set.side_effect = _set
    mock.setex.side_effect = _setex
    mock.delete.side_effect = _delete
    mock.exists.side_effect = _exists
    mock.sadd.side_effect = _sadd
    mock.srem.side_effect = _srem
    mock.smembers.side_effect = _smembers
    mock.keys.side_effect = _keys
    mock.scan_iter.side_effect = _scan_iter
    mock.ttl.side_effect = _ttl_fn
    mock.expire.side_effect = _expire
    mock.ping.side_effect = _ping

    # --- Pipeline ---

    def _make_pipeline(**kwargs):
        pipe = MagicMock()
        commands: list = []

        def pipe_set(name, value, ex=None, **kw):
            commands.append(("set", name, value, ex))
            return pipe

        def pipe_sadd(name, *values):
            commands.append(("sadd", name, values))
            return pipe

        def pipe_delete(*names):
            commands.append(("delete", names))
            return pipe

        def pipe_srem(name, *values):
            commands.append(("srem", name, values))
            return pipe

        def pipe_execute(**kw):
            results = []
            for cmd in commands:
                if cmd[0] == "set":
                    _data[cmd[1]] = cmd[2]
                    if cmd[3] is not None:
                        _ttls[cmd[1]] = cmd[3]
                    results.append(True)
                elif cmd[0] == "sadd":
                    _sets.setdefault(cmd[1], set()).update(cmd[2])
                    results.append(len(cmd[2]))
                elif cmd[0] == "delete":
                    for k in cmd[1]:
                        _data.pop(k, None)
                        _sets.pop(k, None)
                        _ttls.pop(k, None)
                    results.append(len(cmd[1]))
                elif cmd[0] == "srem":
                    for v in cmd[2]:
                        if cmd[1] in _sets:
                            _sets[cmd[1]].discard(v)
                    results.append(len(cmd[2]))
            commands.clear()
            return results

        pipe.set.side_effect = pipe_set
        pipe.sadd.side_effect = pipe_sadd
        pipe.delete.side_effect = pipe_delete
        pipe.srem.side_effect = pipe_srem
        pipe.execute.side_effect = pipe_execute
        return pipe

    mock.pipeline.side_effect = _make_pipeline

    # --- FidesopsRedis-specific methods (used in production compatibility tests) ---

    mock.set_with_autoexpire = MagicMock(
        side_effect=lambda key, value, ex=None: _set(key, value, ex=ex)
    )
    mock.get_keys_by_prefix = MagicMock(
        side_effect=lambda prefix: [k for k in _keys() if k.startswith(prefix)]
    )

    return mock
