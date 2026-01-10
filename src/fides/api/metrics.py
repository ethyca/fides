"""
Simple Prometheus metrics registry for managing application metrics.

This module provides a convenient way to create and retrieve Prometheus metrics
by name, automatically handling registration and preventing duplicates.

Metrics created with this registry are automatically registered with the
Instrumentator's registry and will be exposed via the /api/v1/health/metrics endpoint.
"""

import asyncio
import functools
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, Summary

# Type variable for decorators
F = TypeVar("F", bound=Callable[..., Any])

# Global cache for all metrics to prevent duplicates across instances
_GLOBAL_COUNTERS: Dict[str, Counter] = {}
_GLOBAL_GAUGES: Dict[str, Gauge] = {}
_GLOBAL_HISTOGRAMS: Dict[str, Histogram] = {}
_GLOBAL_SUMMARIES: Dict[str, Summary] = {}


def get_metrics_registry() -> Optional[CollectorRegistry]:
    """
    Get the Prometheus registry from the Instrumentator.

    Returns the Instrumentator's registry if available, otherwise None
    which will use the default prometheus_client REGISTRY.
    """
    try:
        from fides.api.app_setup import get_instrumentator

        instrumentator = get_instrumentator()
        return instrumentator.registry
    except (ImportError, AttributeError, RuntimeError):
        # Fall back to default registry if instrumentator not available
        # or if there's a circular import
        return None


class MetricsRegistry:
    """
    A registry for managing Prometheus metrics with automatic registration.

    This class provides a simple interface to create or retrieve metrics by name,
    ensuring that each metric is only registered once.

    Example:
        >>> registry = MetricsRegistry()
        >>> counter = registry.counter('requests_total', 'Total requests')
        >>> counter.inc()
        >>> gauge = registry.gauge('active_connections', 'Active connections')
        >>> gauge.set(5)
    """

    def __init__(self, registry: Optional[CollectorRegistry] = None) -> None:
        """
        Initialize the metrics registry.

        Args:
            registry: Optional Prometheus CollectorRegistry. If not provided,
                     uses the Instrumentator's registry (or default registry as fallback).
        """
        if registry is None:
            registry = get_metrics_registry()
        self._registry = registry
        # Use global caches to prevent duplicate registrations
        self._counters = _GLOBAL_COUNTERS
        self._gauges = _GLOBAL_GAUGES
        self._histograms = _GLOBAL_HISTOGRAMS
        self._summaries = _GLOBAL_SUMMARIES

    def counter(
        self,
        name: str,
        documentation: str = "",
        labelnames: Optional[List[str]] = None,
        namespace: str = "",
        subsystem: str = "",
    ) -> Counter:
        """
        Get or create a Counter metric.

        Args:
            name: Name of the counter
            documentation: Help text describing the counter
            labelnames: Optional list of label names for the counter
            namespace: Optional namespace for the metric
            subsystem: Optional subsystem for the metric

        Returns:
            Counter instance
        """
        key = self._make_key(name, namespace, subsystem)
        if key not in self._counters:
            try:
                self._counters[key] = Counter(
                    name=name,
                    documentation=documentation or f"Counter for {name}",
                    labelnames=labelnames or [],
                    namespace=namespace,
                    subsystem=subsystem,
                    registry=self._registry,
                )
            except ValueError as e:
                # If metric already exists (e.g., registered by another process),
                # try to retrieve it from the registry
                if "Duplicated timeseries" in str(e) or "already registered" in str(e):
                    # For now, return a dummy counter to avoid crashes
                    # In production, you might want to retrieve the existing metric
                    raise RuntimeError(
                        f"Counter '{key}' already registered with different parameters. "
                        f"This usually means the metric was registered elsewhere with different labels. "
                        f"Error: {e}"
                    ) from e
                raise
        return self._counters[key]

    def gauge(
        self,
        name: str,
        documentation: str = "",
        labelnames: Optional[List[str]] = None,
        namespace: str = "",
        subsystem: str = "",
    ) -> Gauge:
        """
        Get or create a Gauge metric.

        Args:
            name: Name of the gauge
            documentation: Help text describing the gauge
            labelnames: Optional list of label names for the gauge
            namespace: Optional namespace for the metric
            subsystem: Optional subsystem for the metric

        Returns:
            Gauge instance
        """
        key = self._make_key(name, namespace, subsystem)
        if key not in self._gauges:
            try:
                self._gauges[key] = Gauge(
                    name=name,
                    documentation=documentation or f"Gauge for {name}",
                    labelnames=labelnames or [],
                    namespace=namespace,
                    subsystem=subsystem,
                    registry=self._registry,
                )
            except ValueError as e:
                if "Duplicated timeseries" in str(e) or "already registered" in str(e):
                    raise RuntimeError(
                        f"Gauge '{key}' already registered with different parameters. "
                        f"Error: {e}"
                    ) from e
                raise
        return self._gauges[key]

    def histogram(
        self,
        name: str,
        documentation: str = "",
        labelnames: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None,
        namespace: str = "",
        subsystem: str = "",
    ) -> Histogram:
        """
        Get or create a Histogram metric.

        Args:
            name: Name of the histogram
            documentation: Help text describing the histogram
            labelnames: Optional list of label names for the histogram
            buckets: Optional list of bucket boundaries for the histogram
            namespace: Optional namespace for the metric
            subsystem: Optional subsystem for the metric

        Returns:
            Histogram instance
        """
        key = self._make_key(name, namespace, subsystem)
        if key not in self._histograms:
            try:
                kwargs = {
                    "name": name,
                    "documentation": documentation or f"Histogram for {name}",
                    "labelnames": labelnames or [],
                    "namespace": namespace,
                    "subsystem": subsystem,
                    "registry": self._registry,
                }
                if buckets is not None:
                    kwargs["buckets"] = buckets
                self._histograms[key] = Histogram(**kwargs)
            except ValueError as e:
                if "Duplicated timeseries" in str(e) or "already registered" in str(e):
                    raise RuntimeError(
                        f"Histogram '{key}' already registered with different parameters. "
                        f"Error: {e}"
                    ) from e
                raise
        return self._histograms[key]

    def summary(
        self,
        name: str,
        documentation: str = "",
        labelnames: Optional[List[str]] = None,
        namespace: str = "",
        subsystem: str = "",
    ) -> Summary:
        """
        Get or create a Summary metric.

        Args:
            name: Name of the summary
            documentation: Help text describing the summary
            labelnames: Optional list of label names for the summary
            namespace: Optional namespace for the metric
            subsystem: Optional subsystem for the metric

        Returns:
            Summary instance
        """
        key = self._make_key(name, namespace, subsystem)
        if key not in self._summaries:
            try:
                self._summaries[key] = Summary(
                    name=name,
                    documentation=documentation or f"Summary for {name}",
                    labelnames=labelnames or [],
                    namespace=namespace,
                    subsystem=subsystem,
                    registry=self._registry,
                )
            except ValueError as e:
                if "Duplicated timeseries" in str(e) or "already registered" in str(e):
                    raise RuntimeError(
                        f"Summary '{key}' already registered with different parameters. "
                        f"Error: {e}"
                    ) from e
                raise
        return self._summaries[key]

    @staticmethod
    def _make_key(name: str, namespace: str, subsystem: str) -> str:
        """
        Create a unique key for a metric based on its name, namespace, and subsystem.

        Args:
            name: Name of the metric
            namespace: Namespace for the metric
            subsystem: Subsystem for the metric

        Returns:
            Unique key string
        """
        parts = []
        if namespace:
            parts.append(namespace)
        if subsystem:
            parts.append(subsystem)
        parts.append(name)
        return "_".join(parts)

    def has_metric(self, name: str, namespace: str = "", subsystem: str = "") -> bool:
        """
        Check if a metric with the given name already exists.

        Args:
            name: Name of the metric
            namespace: Optional namespace
            subsystem: Optional subsystem

        Returns:
            True if the metric exists, False otherwise
        """
        key = self._make_key(name, namespace, subsystem)
        return (
            key in self._counters
            or key in self._gauges
            or key in self._histograms
            or key in self._summaries
        )

    def clear(self) -> None:
        """
        Clear all cached metrics. Use with caution in production.

        Note: This clears the GLOBAL cache, affecting all MetricsRegistry instances.
        """
        _GLOBAL_COUNTERS.clear()
        _GLOBAL_GAUGES.clear()
        _GLOBAL_HISTOGRAMS.clear()
        _GLOBAL_SUMMARIES.clear()


# Global default registry instance
_default_registry: Optional[MetricsRegistry] = None


def get_default_metrics_registry() -> MetricsRegistry:
    """
    Get the default global metrics registry.

    Returns:
        The default MetricsRegistry instance
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = MetricsRegistry()
    return _default_registry


def count_calls(
    metric_name: Optional[str] = None,
    registry: Optional[MetricsRegistry] = None,
    labels: Optional[Dict[str, str]] = None,
    namespace: str = "",
    subsystem: str = "",
) -> Callable[[F], F]:
    """
    Decorator to count the number of times a function or method is called.

    Args:
        metric_name: Name for the counter metric. If not provided, uses function name.
        registry: MetricsRegistry to use. If not provided, uses default registry.
        labels: Optional dictionary of labels to apply to the counter.
        namespace: Optional namespace for the metric.
        subsystem: Optional subsystem for the metric.

    Returns:
        Decorated function that increments a counter on each call.

    Example:
        >>> @count_calls('api_calls', namespace='myapp')
        ... def handle_request():
        ...     return "OK"

        >>> @count_calls(labels={'method': 'GET'})
        ... async def async_handler():
        ...     return "OK"
    """

    def decorator(func: F) -> F:
        nonlocal metric_name
        if metric_name is None:
            metric_name = f"{func.__name__}_calls_total"

        metrics_registry = registry or get_default_metrics_registry()

        # Determine label names from labels dict
        labelnames = list(labels.keys()) if labels else []

        counter = metrics_registry.counter(
            name=metric_name,
            documentation=f"Total number of calls to {func.__name__}",
            labelnames=labelnames,
            namespace=namespace,
            subsystem=subsystem,
        )

        # Handle async functions
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                if labels:
                    counter.labels(**labels).inc()
                else:
                    counter.inc()
                return await func(*args, **kwargs)

            return cast(F, async_wrapper)

        # Handle sync functions
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            if labels:
                counter.labels(**labels).inc()
            else:
                counter.inc()
            return func(*args, **kwargs)

        return cast(F, sync_wrapper)

    return decorator


def time_calls(
    metric_name: Optional[str] = None,
    registry: Optional[MetricsRegistry] = None,
    labels: Optional[Dict[str, str]] = None,
    buckets: Optional[List[float]] = None,
    namespace: str = "",
    subsystem: str = "",
    use_histogram: bool = True,
) -> Callable[[F], F]:
    """
    Decorator to time function or method execution.

    Uses a Histogram by default to track the distribution of execution times,
    or a Summary if use_histogram=False.

    Args:
        metric_name: Name for the timing metric. If not provided, uses function name.
        registry: MetricsRegistry to use. If not provided, uses default registry.
        labels: Optional dictionary of labels to apply to the metric.
        buckets: Optional bucket boundaries for histogram (ignored if use_histogram=False).
        namespace: Optional namespace for the metric.
        subsystem: Optional subsystem for the metric.
        use_histogram: If True, uses Histogram; if False, uses Summary.

    Returns:
        Decorated function that records execution time.

    Example:
        >>> @time_calls('api_duration_seconds', namespace='myapp')
        ... def handle_request():
        ...     return "OK"

        >>> @time_calls(buckets=[0.1, 0.5, 1.0, 5.0])
        ... async def async_handler():
        ...     return "OK"
    """

    def decorator(func: F) -> F:
        nonlocal metric_name
        if metric_name is None:
            metric_name = f"{func.__name__}_duration_seconds"

        metrics_registry = registry or get_default_metrics_registry()

        # Determine label names from labels dict
        labelnames = list(labels.keys()) if labels else []

        if use_histogram:
            metric = metrics_registry.histogram(
                name=metric_name,
                documentation=f"Execution time of {func.__name__} in seconds",
                labelnames=labelnames,
                buckets=buckets,
                namespace=namespace,
                subsystem=subsystem,
            )
        else:
            metric = metrics_registry.summary(
                name=metric_name,
                documentation=f"Execution time of {func.__name__} in seconds",
                labelnames=labelnames,
                namespace=namespace,
                subsystem=subsystem,
            )

        # Handle async functions
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                start_time = time.perf_counter()
                try:
                    return await func(*args, **kwargs)
                finally:
                    duration = time.perf_counter() - start_time
                    if labels:
                        metric.labels(**labels).observe(duration)
                    else:
                        metric.observe(duration)

            return cast(F, async_wrapper)

        # Handle sync functions
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)

        return cast(F, sync_wrapper)

    return decorator


def count_and_time(
    metric_prefix: Optional[str] = None,
    registry: Optional[MetricsRegistry] = None,
    labels: Optional[Dict[str, str]] = None,
    buckets: Optional[List[float]] = None,
    namespace: str = "",
    subsystem: str = "",
) -> Callable[[F], F]:
    """
    Decorator to both count calls and time execution of a function or method.

    This is a convenience decorator that combines count_calls and time_calls.

    Args:
        metric_prefix: Prefix for metric names. If not provided, uses function name.
        registry: MetricsRegistry to use. If not provided, uses default registry.
        labels: Optional dictionary of labels to apply to metrics.
        buckets: Optional bucket boundaries for the histogram.
        namespace: Optional namespace for metrics.
        subsystem: Optional subsystem for metrics.

    Returns:
        Decorated function that both counts calls and records execution time.

    Example:
        >>> @count_and_time('api_request', namespace='myapp')
        ... def handle_request():
        ...     return "OK"

        >>> @count_and_time()
        ... async def async_handler():
        ...     return "OK"
    """

    def decorator(func: F) -> F:
        nonlocal metric_prefix
        if metric_prefix is None:
            metric_prefix = func.__name__

        # Apply both decorators
        counted = count_calls(
            metric_name=f"{metric_prefix}_calls_total",
            registry=registry,
            labels=labels,
            namespace=namespace,
            subsystem=subsystem,
        )(func)

        timed = time_calls(
            metric_name=f"{metric_prefix}_duration_seconds",
            registry=registry,
            labels=labels,
            buckets=buckets,
            namespace=namespace,
            subsystem=subsystem,
        )(counted)

        return timed

    return decorator
