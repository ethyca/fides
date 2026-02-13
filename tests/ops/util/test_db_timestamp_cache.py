"""Tests for fides.api.util.db_timestamp_cache.

Covers:
- Cache miss behavior (first call, after clear, after DB state change)
- Cache hit behavior (unchanged DB state)
- Invalidation via updated_at change
- Invalidation via count change (detects deletions)
- Manual cache_clear() forcing reload
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from fides.api.util.db_timestamp_cache import _cache_store, db_timestamp_cached

CACHE_KEY = "test_cache"


@pytest.fixture(autouse=True)
def clear_cache():
    """Ensure each test starts with a clean cache and cleans up after."""
    _cache_store.pop(CACHE_KEY, None)
    yield
    _cache_store.pop(CACHE_KEY, None)


@pytest.fixture
def mock_model():
    """A stand-in for a SQLAlchemy model class passed to the decorator."""
    return MagicMock()


@pytest.fixture
def mock_get_table_state():
    """Patch _get_table_state so no real DB session is needed."""
    with patch("fides.api.util.db_timestamp_cache._get_table_state") as mock:
        yield mock


class TestCacheMissBehavior:
    """First call or stale cache should invoke the decorated function."""

    def test_first_call_invokes_function_and_caches_result(
        self, mock_model, mock_get_table_state
    ):
        """On a cold cache the decorated function must be called and its
        return value cached."""
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        mock_get_table_state.return_value = (now, 3)

        inner = MagicMock(return_value={"a": 1})

        decorated = db_timestamp_cached(model=mock_model, cache_key=CACHE_KEY)(inner)
        result = decorated()

        assert result == {"a": 1}
        inner.assert_called_once()

    def test_function_return_value_is_preserved_exactly(
        self, mock_model, mock_get_table_state
    ):
        """The decorator must not alter the return value."""
        mock_get_table_state.return_value = (None, 0)
        expected = [{"key": "val"}, 42, None]

        decorated = db_timestamp_cached(model=mock_model, cache_key=CACHE_KEY)(
            lambda: expected
        )

        assert decorated() is expected


class TestCacheHitBehavior:
    """When DB state is unchanged the cached value is returned without
    re-calling the function."""

    def test_second_call_returns_cached_value_without_calling_function(
        self, mock_model, mock_get_table_state
    ):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        mock_get_table_state.return_value = (now, 5)

        call_count = 0

        def counting_fn():
            nonlocal call_count
            call_count += 1
            return {"data": call_count}

        decorated = db_timestamp_cached(model=mock_model, cache_key=CACHE_KEY)(
            counting_fn
        )

        first = decorated()
        second = decorated()

        assert first == {"data": 1}
        assert second == {"data": 1}  # same cached value
        assert call_count == 1  # function only called once


class TestInvalidationByUpdatedAt:
    """A change in MAX(updated_at) must trigger a reload."""

    def test_updated_at_change_triggers_reload(self, mock_model, mock_get_table_state):
        t1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        t2 = datetime(2026, 1, 2, tzinfo=timezone.utc)

        call_count = 0

        def counting_fn():
            nonlocal call_count
            call_count += 1
            return f"version_{call_count}"

        decorated = db_timestamp_cached(model=mock_model, cache_key=CACHE_KEY)(
            counting_fn
        )

        # First call: t1, count=2
        mock_get_table_state.return_value = (t1, 2)
        assert decorated() == "version_1"

        # Second call: updated_at changed to t2, same count
        mock_get_table_state.return_value = (t2, 2)
        assert decorated() == "version_2"
        assert call_count == 2


class TestInvalidationByCount:
    """A change in COUNT(*) (e.g. a row deletion) must trigger a reload,
    even if MAX(updated_at) stays the same."""

    def test_count_decrease_triggers_reload(self, mock_model, mock_get_table_state):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)

        call_count = 0

        def counting_fn():
            nonlocal call_count
            call_count += 1
            return f"version_{call_count}"

        decorated = db_timestamp_cached(model=mock_model, cache_key=CACHE_KEY)(
            counting_fn
        )

        # First call: 3 rows
        mock_get_table_state.return_value = (now, 3)
        assert decorated() == "version_1"

        # Row deleted: count drops to 2 but max_updated_at unchanged
        mock_get_table_state.return_value = (now, 2)
        assert decorated() == "version_2"
        assert call_count == 2

    def test_count_increase_triggers_reload(self, mock_model, mock_get_table_state):
        """New row added with an older updated_at than the current max
        would not change MAX(updated_at) but should still invalidate."""
        now = datetime(2026, 6, 1, tzinfo=timezone.utc)

        call_count = 0

        def counting_fn():
            nonlocal call_count
            call_count += 1
            return call_count

        decorated = db_timestamp_cached(model=mock_model, cache_key=CACHE_KEY)(
            counting_fn
        )

        mock_get_table_state.return_value = (now, 1)
        assert decorated() == 1

        # Count increased but max_updated_at unchanged (edge case)
        mock_get_table_state.return_value = (now, 2)
        assert decorated() == 2
        assert call_count == 2


class TestCacheClear:
    """Manual cache_clear() must force a reload on the next call."""

    def test_cache_clear_forces_reload(self, mock_model, mock_get_table_state):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        mock_get_table_state.return_value = (now, 1)

        call_count = 0

        def counting_fn():
            nonlocal call_count
            call_count += 1
            return call_count

        decorated = db_timestamp_cached(model=mock_model, cache_key=CACHE_KEY)(
            counting_fn
        )

        assert decorated() == 1
        assert call_count == 1

        # DB state unchanged, but we manually clear
        decorated.cache_clear()

        assert decorated() == 2
        assert call_count == 2

    def test_cache_clear_is_idempotent(self, mock_model, mock_get_table_state):
        """Calling cache_clear() when the cache is already empty should not
        raise an error."""
        decorated = db_timestamp_cached(model=mock_model, cache_key=CACHE_KEY)(
            lambda: None
        )

        # Clear on empty cache — should be a no-op
        decorated.cache_clear()
        decorated.cache_clear()
