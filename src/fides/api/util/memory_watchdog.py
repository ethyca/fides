"""
Memory watchdog utilities used to proactively interrupt long-running Celery tasks that approach the
container's memory limits.

The watchdog runs in a background thread and periodically samples the overall system memory usage
(using `psutil`). When usage exceeds the configured threshold, it immediately sends `SIGUSR1` to
the current process. The signal handler raises `MemoryLimitExceeded` which can be caught by the
calling code to perform clean-up and let Celery record the task as failed.

This allows tasks to terminate gracefully with proper error logging, rather than being forcefully
killed by the system's OOM killer which would result in a WorkerLostError and incomplete cleanup.
"""

from __future__ import annotations

import os
import signal
import threading
import time
from functools import wraps
from types import FrameType, TracebackType
from typing import Any, Callable, Literal, Optional, Type, TypeVar, Union

import psutil  # type: ignore
from loguru import logger

F = TypeVar("F", bound=Callable[..., Any])


def get_memory_watchdog_enabled() -> bool:
    """
    Get the memory_watchdog_enabled setting from the application configuration.

    Returns:
        bool: True if memory_watchdog_enabled is enabled, False otherwise (defaults to False)
    """
    try:
        from fides.api.api.deps import get_autoclose_db_session as get_db
        from fides.config.config_proxy import ConfigProxy

        with get_db() as db:
            config_proxy = ConfigProxy(db)
            # ConfigProxy returns None when no config record exists, so we must handle None explicitly
            value = getattr(config_proxy.execution, "memory_watchdog_enabled")
            return value if value is not None else False
    except Exception:  # pragma: no cover
        # default to disabled for backward compatibility
        return False


class MemoryLimitExceeded(RuntimeError):
    """Raised when the watchdog detects sustained memory usage above the threshold."""

    def __init__(self, message: str, *, memory_percent: Optional[float] = None) -> None:
        super().__init__(message)
        self.memory_percent: Optional[float] = memory_percent


class MemoryWatchdog:
    """Background memory monitor that enables graceful task termination.

    Monitors system memory usage and triggers controlled shutdown when usage exceeds the threshold,
    preventing forceful termination by the system's OOM killer.

    Parameters
    ----------
    threshold:
        Percentage of *overall* system memory usage at which the watchdog triggers.
    check_interval:
        How often (in seconds) to sample ``psutil.virtual_memory()``.
    grace_period:
        Deprecated - kept for compatibility but defaults to 0 for immediate action.
    """

    def __init__(
        self, *, threshold: int = 90, check_interval: float = 0.5, grace_period: int = 0
    ) -> None:
        self.threshold = threshold
        self.check_interval = check_interval
        self.grace_period = grace_period

        self._thread: Optional[threading.Thread] = None
        self._monitoring = threading.Event()
        self._original_handler: Union[
            Callable[[int, Optional[FrameType]], Any], int, signal.Handlers, None
        ] = None

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------
    def start(self) -> None:
        """Start the background monitoring thread and register the signal handler."""
        logger.debug(
            "Starting memory watchdog - threshold={}%, check_interval={}s",
            self.threshold,
            self.check_interval,
        )
        self._original_handler = signal.signal(signal.SIGUSR1, self._signal_handler)
        self._monitoring.set()
        self._thread = threading.Thread(
            target=self._run, name="memory-watchdog", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the monitoring thread and restore the previous signal handler."""
        logger.debug("Stopping memory watchdog")
        self._monitoring.clear()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        if self._original_handler is not None:
            signal.signal(signal.SIGUSR1, self._original_handler)
            self._original_handler = None

    # ------------------------------------------------------------------
    # Context-manager support
    # ------------------------------------------------------------------
    def __enter__(self) -> "MemoryWatchdog":
        self.start()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Literal[False]:
        self.stop()
        # Do not suppress exceptions
        return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _signal_handler(
        self, signum: int, frame: Optional[FrameType]
    ) -> None:  # noqa: D401 – Celery uses signal handlers
        """Convert the signal into an exception on the main thread."""
        current_percent = _system_memory_percent()
        logger.error("Memory limit exceeded: {}%", current_percent)
        self.stop()
        raise MemoryLimitExceeded(
            "Memory usage exceeded threshold", memory_percent=current_percent
        )

    def _run(self) -> None:
        """Background thread body."""
        while self._monitoring.is_set():
            try:
                mem_percent = _system_memory_percent()

                if mem_percent > self.threshold:
                    # Trigger graceful termination before the system OOM killer can intervene
                    logger.error(
                        "Memory usage {}% above threshold {}% - sending SIGUSR1 to terminate task gracefully (prevents OOM kill)",
                        mem_percent,
                        self.threshold,
                    )
                    os.kill(os.getpid(), signal.SIGUSR1)
                    return  # stop monitoring after signal

                time.sleep(self.check_interval)
            except Exception as exc:  # pragma: no cover – best-effort logging
                logger.exception("Uncaught error in memory watchdog: {}", exc)
                break


# -----------------------------------------------------------------------------
# Decorator for Celery tasks (or any function)
# -----------------------------------------------------------------------------


def memory_limiter(
    _func: Optional[F] = None,
    *,
    threshold: int = 90,
    check_interval: float = 0.5,
    grace_period: int = 0,
) -> Union[F, Callable[[F], F]]:
    """Decorator that runs the wrapped callable under a :class:`MemoryWatchdog`.

    Enables graceful task termination when memory usage is high, preventing WorkerLostError
    from system OOM killer intervention.

    Can be applied **with or without arguments**::

        @memory_limiter
        def task_a():
            ...

        @memory_limiter(threshold=85)
        def task_b():
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Check if memory watchdog is enabled
            if not get_memory_watchdog_enabled():
                logger.debug(
                    "Memory watchdog disabled by configuration - running task without monitoring"
                )
                return func(*args, **kwargs)

            watchdog = MemoryWatchdog(
                threshold=threshold,
                check_interval=check_interval,
                grace_period=grace_period,
            )
            watchdog.start()
            try:
                return func(*args, **kwargs)
            except MemoryLimitExceeded as exc:
                logger.error(
                    "Task terminated gracefully due to memory pressure: {}%",
                    exc.memory_percent,
                )
                raise
            finally:
                watchdog.stop()

        return wrapper  # type: ignore[return-value]

    # If called without arguments, the first positional argument is the function
    if _func is not None and callable(_func):
        return decorator(_func)

    return decorator


# -----------------------------------------------------------------------------
# Platform helpers – cgroup-aware memory measurement
# -----------------------------------------------------------------------------

# Docker / Kubernetes containers are usually memory-constrained via cgroups.  If we only look at
# host-wide memory usage the watchdog will never fire, because the host may still have plenty of
# free RAM even though the container is about to be OOM-killed.  The helpers below read the
# relevant cgroup files (v2 first, then v1) and compute the percentage of the *container limit* in
# use.  When cgroup information is unavailable (e.g. running directly on the host) we return
# `None` and fall back to `psutil`.


def _cgroup_memory_percent() -> Optional[float]:
    """Return container memory usage as *percentage* of the cgroup limit or `None` when not
    running inside a memory-limited cgroup."""

    def _read(path: str) -> Optional[int]:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                raw = fh.read().strip()
                if raw == "" or raw.lower() == "max":  # v2 "max" means unlimited
                    return None
                return int(raw)
        except (FileNotFoundError, PermissionError, ValueError):  # pragma: no cover
            return None

    # cgroups v2 (unified)
    usage = _read("/sys/fs/cgroup/memory.current")
    limit = _read("/sys/fs/cgroup/memory.max")
    if usage is not None and limit and limit > 0:
        return usage / limit * 100

    # cgroups v1
    usage = _read("/sys/fs/cgroup/memory/memory.usage_in_bytes")
    limit = _read("/sys/fs/cgroup/memory/memory.limit_in_bytes")
    if (
        usage is not None and limit and 0 < limit < (1 << 60)
    ):  # ignore enormous "unlimited" value
        return usage / limit * 100

    return None


def _system_memory_percent() -> float:
    """Best-effort *current* memory usage percentage for the running worker.

    1. Use cgroup metrics when they are available and meaningful.
    2. Fall back to host-wide `psutil.virtual_memory().percent` otherwise."""

    cgroup_percent = _cgroup_memory_percent()
    if cgroup_percent is not None:
        return cgroup_percent

    # Fall back to host memory usage
    return psutil.virtual_memory().percent
