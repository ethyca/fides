"""
Memory tracking utilities for DSR tasks to diagnose OOM issues.

This module provides detailed memory tracking for individual DSR tasks to help identify:
1. Per-task peak memory usage (OOM during a specific big job)
2. Memory creep across tasks (high-water mark / baseline rises)

Tracked Metrics:
- RSS (Resident Set Size) before and after task
- Payload size (rows processed)
- tracemalloc current memory
- SQLAlchemy identity_map size
- Task execution time

Usage:
    from fides.api.util.dsr_memory_tracker import track_dsr_task_memory

    @celery_app.task(base=DatabaseTask, bind=True)
    @track_dsr_task_memory()
    def my_dsr_task(self, privacy_request_id, ...):
        ...
"""

from __future__ import annotations

import gc
import os
import sys
import tracemalloc
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Generator, List, Optional, TypeVar

import psutil  # type: ignore
from loguru import logger
from sqlalchemy import inspect
from sqlalchemy.orm import Session

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class MemorySnapshot:
    """Snapshot of memory metrics at a point in time."""

    timestamp: str
    # Process memory (RSS) in MB
    rss_before: float
    rss_after: float
    rss_after_gc: float
    # Python memory allocator (tracemalloc) in MB
    tracemalloc_current: float = 0.0
    tracemalloc_peak: float = 0.0
    # SQLAlchemy session state
    sqlalchemy_identity_map_size: int = 0
    # Python garbage collector counts
    gc_counts: Dict[str, int] = field(default_factory=dict)


@dataclass
class TaskMemoryMetrics:
    """Complete memory metrics for a task execution."""

    # Task identification
    task_name: str
    task_id: str
    pid: int
    queue: str = ""
    privacy_request_id: Optional[str] = None
    privacy_request_task_id: Optional[str] = None
    collection_address: Optional[str] = None

    # Execution timing
    start_time: str = ""
    end_time: str = ""
    duration_seconds: float = 0.0
    duration_ms: float = 0.0

    # Memory metrics (MB)
    rss_before: float = 0.0
    rss_after: float = 0.0
    rss_after_gc: float = 0.0
    tracemalloc_current: float = 0.0
    tracemalloc_peak: float = 0.0

    # SQLAlchemy session state
    sqlalchemy_identity_map_size: int = 0

    # GC counts
    gc_counts: Dict[str, int] = field(default_factory=dict)

    # Data payload metrics
    payload_size_bytes: int = 0
    rows: int = 0

    # Status
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for logging."""
        return asdict(self)


class MemoryTracker:
    """Utility to capture memory metrics."""

    def __init__(self, enable_tracemalloc: bool = True):
        self.enable_tracemalloc = enable_tracemalloc
        self._tracemalloc_started = False
        self.process = psutil.Process()

    def start_tracemalloc(self) -> None:
        """Start tracemalloc if enabled and not already started."""
        if self.enable_tracemalloc and not tracemalloc.is_tracing():
            tracemalloc.start()
            self._tracemalloc_started = True

    def stop_tracemalloc(self) -> None:
        """Stop tracemalloc if we started it."""
        if self._tracemalloc_started and tracemalloc.is_tracing():
            tracemalloc.stop()
            self._tracemalloc_started = False

    def get_snapshot(self, session: Optional[Session] = None) -> MemorySnapshot:
        """Capture current memory metrics with before/after/after_gc RSS."""
        # Get RSS before
        mem_info = self.process.memory_info()
        rss_before = mem_info.rss / (1024 * 1024)

        # Get RSS after (immediate)
        mem_info = self.process.memory_info()
        rss_after = mem_info.rss / (1024 * 1024)

        # Force garbage collection and get RSS after GC
        gc.collect()
        mem_info = self.process.memory_info()
        rss_after_gc = mem_info.rss / (1024 * 1024)

        # tracemalloc memory
        tracemalloc_current = 0.0
        tracemalloc_peak = 0.0
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc_current = current / (1024 * 1024)
            tracemalloc_peak = peak / (1024 * 1024)

        # SQLAlchemy identity map
        sqlalchemy_identity_map_size = 0
        if session is not None:
            try:
                if hasattr(session, "identity_map"):
                    sqlalchemy_identity_map_size = len(session.identity_map)
            except Exception as e:
                logger.debug(f"Could not get identity_map size: {e}")

        # GC counts (number of objects in each generation)
        gc_count = gc.get_count()
        gc_counts = {
            "gen0": gc_count[0],
            "gen1": gc_count[1],
            "gen2": gc_count[2],
        }

        return MemorySnapshot(
            timestamp=datetime.utcnow().isoformat(),
            rss_before=round(rss_before, 2),
            rss_after=round(rss_after, 2),
            rss_after_gc=round(rss_after_gc, 2),
            tracemalloc_current=round(tracemalloc_current, 2),
            tracemalloc_peak=round(tracemalloc_peak, 2),
            sqlalchemy_identity_map_size=sqlalchemy_identity_map_size,
            gc_counts=gc_counts,
        )

    def estimate_payload_size(self, data: Any) -> int:
        """
        Estimate the size of a data payload in bytes.

        This is a rough estimate using sys.getsizeof recursively for common data structures.
        """
        if data is None:
            return 0

        seen = set()

        def sizeof(obj: Any) -> int:
            """Recursive sizeof for nested structures."""
            obj_id = id(obj)
            if obj_id in seen:
                return 0
            seen.add(obj_id)

            size = sys.getsizeof(obj)

            if isinstance(obj, dict):
                size += sum(sizeof(k) + sizeof(v) for k, v in obj.items())
            elif isinstance(obj, (list, tuple, set)):
                size += sum(sizeof(item) for item in obj)

            return size

        try:
            return sizeof(data)
        except Exception as e:
            logger.debug(f"Could not estimate payload size: {e}")
            return 0

    def count_rows(self, data: Any) -> int:
        """
        Count the number of rows in various data structures.

        Handles:
        - List of dicts (common DSR format)
        - Dict of lists
        - Single dict
        - List of lists
        """
        if data is None:
            return 0

        try:
            if isinstance(data, list):
                return len(data)
            elif isinstance(data, dict):
                # If dict values are lists, sum their lengths
                if data and isinstance(next(iter(data.values()), None), list):
                    return sum(len(v) for v in data.values() if isinstance(v, list))
                return 1
            return 0
        except Exception as e:
            logger.debug(f"Could not count rows: {e}")
            return 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary - kept for backwards compatibility."""
        return {}


@contextmanager
def memory_tracking_context(
    task_name: str,
    task_id: str,
    privacy_request_id: Optional[str] = None,
    privacy_request_task_id: Optional[str] = None,
    collection_address: Optional[str] = None,
    session: Optional[Session] = None,
    enable_tracemalloc: bool = True,
) -> Generator[TaskMemoryMetrics, None, None]:
    """
    Context manager for tracking memory during a task execution.

    Usage:
        with memory_tracking_context("my_task", task_id, session=session) as metrics:
            # Do work
            result = process_data()
            # Update metrics
            metrics.rows_processed = len(result)
            metrics.payload_size_bytes = tracker.estimate_payload_size(result)
    """
    # Check if tracking is enabled
    enabled = os.environ.get("FIDES__DSR_MEMORY_TRACKING_ENABLED", "false").lower() in (
        "true",
        "1",
        "yes",
    )

    # If disabled, provide a no-op context
    if not enabled:
        metrics = TaskMemoryMetrics(
            task_name=task_name,
            task_id=task_id,
            privacy_request_id=privacy_request_id,
            privacy_request_task_id=privacy_request_task_id,
            collection_address=collection_address,
        )
        yield metrics
        return

    tracker = MemoryTracker(enable_tracemalloc=enable_tracemalloc)
    tracker.start_tracemalloc()

    # Get process info
    pid = os.getpid()

    # Try to get queue name from Celery context
    queue_name = "unknown"
    try:
        from celery import current_task
        if current_task and hasattr(current_task.request, 'delivery_info'):
            queue_name = current_task.request.delivery_info.get('routing_key', 'unknown')
    except Exception:
        pass

    metrics = TaskMemoryMetrics(
        task_name=task_name,
        task_id=task_id,
        pid=pid,
        queue=queue_name,
        privacy_request_id=privacy_request_id,
        privacy_request_task_id=privacy_request_task_id,
        collection_address=collection_address,
        start_time=datetime.utcnow().isoformat(),
    )

    # Capture before snapshot
    snapshot = tracker.get_snapshot(session)
    metrics.rss_before = snapshot.rss_before
    metrics.tracemalloc_current = snapshot.tracemalloc_current
    metrics.tracemalloc_peak = snapshot.tracemalloc_peak
    metrics.sqlalchemy_identity_map_size = snapshot.sqlalchemy_identity_map_size
    metrics.gc_counts = snapshot.gc_counts

    try:
        yield metrics
    except Exception as e:
        metrics.success = False
        metrics.error = str(e)
        raise
    finally:
        # Capture after snapshot
        metrics.end_time = datetime.utcnow().isoformat()
        snapshot = tracker.get_snapshot(session)
        metrics.rss_after = snapshot.rss_after
        metrics.rss_after_gc = snapshot.rss_after_gc

        # Update tracemalloc peak if higher
        if snapshot.tracemalloc_peak > metrics.tracemalloc_peak:
            metrics.tracemalloc_peak = snapshot.tracemalloc_peak

        # Calculate duration
        try:
            start = datetime.fromisoformat(metrics.start_time)
            end = datetime.fromisoformat(metrics.end_time)
            duration_sec = (end - start).total_seconds()
            metrics.duration_seconds = duration_sec
            metrics.duration_ms = duration_sec * 1000
        except Exception:
            pass

        # Log the metrics
        _log_task_memory_metrics(metrics)

        tracker.stop_tracemalloc()


def track_dsr_task_memory(
    enable_tracemalloc: bool = True,
) -> Callable[[F], F]:
    """
    Decorator to track memory for DSR tasks.

    This decorator automatically extracts common DSR task parameters and tracks memory.
    It expects the task to be a Celery task with DatabaseTask base.

    Args:
        enable_tracemalloc: Whether to enable tracemalloc tracking (default: True)

    Usage:
        @celery_app.task(base=DatabaseTask, bind=True)
        @track_dsr_task_memory()
        def run_access_node(self, privacy_request_id, privacy_request_task_id, ...):
            ...

    Environment Variables:
        FIDES__DSR_MEMORY_TRACKING_ENABLED: Set to "true" to enable (default: false)
        FIDES__DSR_MEMORY_TRACKING_TRACEMALLOC: Set to "true" to enable tracemalloc (default: true)
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Check if memory tracking is enabled
            enabled = os.environ.get("FIDES__DSR_MEMORY_TRACKING_ENABLED", "false").lower() in (
                "true",
                "1",
                "yes",
            )
            if not enabled:
                return func(*args, **kwargs)

            # Check tracemalloc setting
            use_tracemalloc = enable_tracemalloc and os.environ.get(
                "FIDES__DSR_MEMORY_TRACKING_TRACEMALLOC", "true"
            ).lower() in ("true", "1", "yes")

            # Extract task info
            # For Celery tasks, self is the task instance with request context
            task_instance = args[0] if args else None
            task_id = getattr(task_instance, "request", {}).get("id", "unknown")
            task_name = func.__name__

            # Extract common DSR parameters
            privacy_request_id = kwargs.get("privacy_request_id")
            privacy_request_task_id = kwargs.get("privacy_request_task_id")

            # Try to get session if task has get_new_session
            session = None
            collection_address = None

            with memory_tracking_context(
                task_name=task_name,
                task_id=task_id,
                privacy_request_id=privacy_request_id,
                privacy_request_task_id=privacy_request_task_id,
                collection_address=collection_address,
                session=session,
                enable_tracemalloc=use_tracemalloc,
            ) as metrics:
                result = func(*args, **kwargs)

                # Try to extract metrics from result if possible
                # This is task-specific and may need customization
                if result is not None:
                    tracker = MemoryTracker()
                    metrics.rows = tracker.count_rows(result)
                    metrics.payload_size_bytes = tracker.estimate_payload_size(result)

                return result

        return wrapper  # type: ignore[return-value]

    return decorator


def _log_task_memory_metrics(metrics: TaskMemoryMetrics) -> None:
    """
    Log task memory metrics in a structured format.

    Uses a special log level and structure for easy parsing/analysis.
    """
    # Calculate deltas for summary
    rss_delta = metrics.rss_after - metrics.rss_before
    rss_gc_freed = metrics.rss_after - metrics.rss_after_gc

    # Create a summary for quick scanning
    summary = (
        f"Task: {metrics.task_name} | "
        f"RSS: {metrics.rss_before:.1f}→{metrics.rss_after:.1f}→{metrics.rss_after_gc:.1f}MB "
        f"(Δ{rss_delta:+.1f}, GC freed {rss_gc_freed:.1f}) | "
        f"Rows: {metrics.rows} | "
        f"Payload: {metrics.payload_size_bytes / (1024*1024):.1f}MB | "
        f"Duration: {metrics.duration_ms:.0f}ms | "
        f"IdentityMap: {metrics.sqlalchemy_identity_map_size}"
    )

    if not metrics.success:
        summary += f" | ERROR: {metrics.error}"

    # Log with special marker for easy filtering
    logger.bind(
        dsr_memory_metrics=True,
        task_name=metrics.task_name,
        task_id=metrics.task_id,
        pid=metrics.pid,
        queue=metrics.queue,
        privacy_request_id=metrics.privacy_request_id,
        privacy_request_task_id=metrics.privacy_request_task_id,
        collection_address=metrics.collection_address,
    ).info(f"[DSR_MEMORY] {summary}")

    # Log full metrics at debug level for detailed analysis
    logger.bind(dsr_memory_metrics=True).debug(
        f"[DSR_MEMORY_FULL] {metrics.to_dict()}"
    )


# Convenience function for manual tracking in specific code sections
def log_memory_snapshot(
    label: str,
    session: Optional[Session] = None,
    extra_data: Optional[Dict[str, Any]] = None,
) -> MemorySnapshot:
    """
    Manually log a memory snapshot with a label.

    Useful for tracking memory at specific points within a task.

    Usage:
        snapshot = log_memory_snapshot("after_big_query", session=session)
        logger.info(f"Memory at checkpoint: {snapshot.rss_after_gc}MB")
    """
    tracker = MemoryTracker(enable_tracemalloc=False)
    snapshot = tracker.get_snapshot(session)

    logger.bind(
        dsr_memory_snapshot=True,
        snapshot_label=label,
        **(extra_data or {}),
    ).info(
        f"[DSR_MEMORY_SNAPSHOT] {label}: RSS={snapshot.rss_after_gc}MB, "
        f"Identity Map={snapshot.sqlalchemy_identity_map_size}"
    )

    return snapshot
