"""Tests for DSR memory tracking utilities."""

import os
from unittest.mock import Mock, patch

import pytest

from fides.api.util.dsr_memory_tracker import (
    MemorySnapshot,
    MemoryTracker,
    TaskMemoryMetrics,
    memory_tracking_context,
)


class TestMemoryTracker:
    """Test the MemoryTracker class."""

    def test_get_snapshot_basic(self):
        """Test basic snapshot capture."""
        tracker = MemoryTracker(enable_tracemalloc=False)
        snapshot = tracker.get_snapshot()

        assert isinstance(snapshot, MemorySnapshot)
        assert snapshot.rss_mb > 0
        assert snapshot.rss_percent > 0
        assert snapshot.timestamp is not None

    def test_get_snapshot_with_tracemalloc(self):
        """Test snapshot with tracemalloc enabled."""
        tracker = MemoryTracker(enable_tracemalloc=True)
        tracker.start_tracemalloc()

        try:
            snapshot = tracker.get_snapshot()

            assert snapshot.tracemalloc_current_mb >= 0
            assert snapshot.tracemalloc_peak_mb >= 0
        finally:
            tracker.stop_tracemalloc()

    def test_estimate_payload_size(self):
        """Test payload size estimation."""
        tracker = MemoryTracker()

        # Test with simple data structures
        data = {"key": "value", "list": [1, 2, 3]}
        size = tracker.estimate_payload_size(data)
        assert size > 0

        # Test with None
        assert tracker.estimate_payload_size(None) == 0

    def test_count_rows(self):
        """Test row counting."""
        tracker = MemoryTracker()

        # List of dicts (common DSR format)
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        assert tracker.count_rows(data) == 3

        # Dict of lists
        data = {"users": [1, 2, 3], "orders": [4, 5]}
        assert tracker.count_rows(data) == 5

        # Single dict
        data = {"id": 1}
        assert tracker.count_rows(data) == 1

        # None
        assert tracker.count_rows(None) == 0


class TestMemoryTrackingContext:
    """Test the memory_tracking_context context manager."""

    @patch.dict(os.environ, {"FIDES__DSR_MEMORY_TRACKING_ENABLED": "false"})
    def test_context_disabled(self):
        """Test that context is no-op when disabled."""
        with memory_tracking_context(
            task_name="test_task",
            task_id="test_id",
        ) as metrics:
            assert isinstance(metrics, TaskMemoryMetrics)
            assert metrics.task_name == "test_task"
            assert metrics.before is None  # No tracking when disabled

    @patch.dict(os.environ, {"FIDES__DSR_MEMORY_TRACKING_ENABLED": "true"})
    def test_context_enabled(self):
        """Test that context tracks metrics when enabled."""
        with memory_tracking_context(
            task_name="test_task",
            task_id="test_id",
            privacy_request_id="pri_test",
            enable_tracemalloc=False,  # Disable for test speed
        ) as metrics:
            assert isinstance(metrics, TaskMemoryMetrics)
            assert metrics.task_name == "test_task"
            assert metrics.task_id == "test_id"
            assert metrics.privacy_request_id == "pri_test"

            # Do some work
            data = [{"id": i} for i in range(100)]
            metrics.rows_processed = len(data)

        # After context, should have snapshots
        assert metrics.before is not None
        assert metrics.after is not None
        assert metrics.duration_seconds > 0
        assert metrics.rows_processed == 100

    @patch.dict(os.environ, {"FIDES__DSR_MEMORY_TRACKING_ENABLED": "true"})
    def test_context_with_exception(self):
        """Test that context handles exceptions properly."""
        with pytest.raises(ValueError):
            with memory_tracking_context(
                task_name="test_task",
                task_id="test_id",
                enable_tracemalloc=False,
            ) as metrics:
                raise ValueError("Test error")

        # Should still have captured metrics
        assert metrics.success is False
        assert metrics.error == "Test error"
        assert metrics.before is not None
        assert metrics.after is not None

    @patch.dict(os.environ, {"FIDES__DSR_MEMORY_TRACKING_ENABLED": "true"})
    def test_context_calculates_deltas(self):
        """Test that context calculates memory deltas."""
        with memory_tracking_context(
            task_name="test_task",
            task_id="test_id",
            enable_tracemalloc=False,
        ) as metrics:
            # Allocate some memory
            _ = [{"data": "x" * 1000} for _ in range(1000)]

        # Should have calculated deltas
        assert metrics.rss_delta_mb != 0  # Memory changed
        assert metrics.duration_seconds > 0


class TestTaskMemoryMetrics:
    """Test the TaskMemoryMetrics dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metrics = TaskMemoryMetrics(
            task_name="test_task",
            task_id="test_id",
            rows_processed=100,
        )

        result = metrics.to_dict()
        assert isinstance(result, dict)
        assert result["task_name"] == "test_task"
        assert result["task_id"] == "test_id"
        assert result["rows_processed"] == 100

    def test_to_dict_with_snapshots(self):
        """Test dictionary conversion with before/after snapshots."""
        before = MemorySnapshot(
            timestamp="2026-01-15T10:00:00",
            rss_mb=100.0,
            rss_percent=10.0,
            identity_map_size=50,
        )
        after = MemorySnapshot(
            timestamp="2026-01-15T10:00:05",
            rss_mb=150.0,
            rss_percent=15.0,
            identity_map_size=150,
        )

        metrics = TaskMemoryMetrics(
            task_name="test_task",
            task_id="test_id",
            before=before,
            after=after,
        )

        result = metrics.to_dict()
        assert result["rss_delta_mb"] == 50.0
        assert result["identity_map_delta"] == 100
