"""
Unit tests for the MetricsRegistry.
"""

import asyncio
import time

import pytest
from prometheus_client import CollectorRegistry

from fides.api.metrics import (
    MetricsRegistry,
    count_and_time,
    count_calls,
    get_default_metrics_registry,
    time_calls,
)


class TestMetricsRegistry:
    """Test suite for MetricsRegistry."""

    def test_counter_creation(self) -> None:
        """Test that counters are created and retrieved correctly."""
        registry = MetricsRegistry(registry=CollectorRegistry())

        counter1 = registry.counter("test_counter", "Test counter")
        counter2 = registry.counter("test_counter")

        # Should return the same instance
        assert counter1 is counter2

        # Should be usable
        counter1.inc()
        assert counter1._value.get() == 1

    def test_gauge_creation(self) -> None:
        """Test that gauges are created and retrieved correctly."""
        registry = MetricsRegistry(registry=CollectorRegistry())

        gauge1 = registry.gauge("test_gauge", "Test gauge")
        gauge2 = registry.gauge("test_gauge")

        # Should return the same instance
        assert gauge1 is gauge2

        # Should be usable
        gauge1.set(42)
        assert gauge1._value.get() == 42

    def test_histogram_creation(self) -> None:
        """Test that histograms are created and retrieved correctly."""
        registry = MetricsRegistry(registry=CollectorRegistry())

        histogram1 = registry.histogram("test_histogram", "Test histogram")
        histogram2 = registry.histogram("test_histogram")

        # Should return the same instance
        assert histogram1 is histogram2

        # Should be usable
        histogram1.observe(0.5)
        assert histogram1._count.get() == 1

    def test_summary_creation(self) -> None:
        """Test that summaries are created and retrieved correctly."""
        registry = MetricsRegistry(registry=CollectorRegistry())

        summary1 = registry.summary("test_summary", "Test summary")
        summary2 = registry.summary("test_summary")

        # Should return the same instance
        assert summary1 is summary2

        # Should be usable
        summary1.observe(100)
        assert summary1._count.get() == 1

    def test_counter_with_labels(self) -> None:
        """Test that counters with labels work correctly."""
        registry = MetricsRegistry(registry=CollectorRegistry())

        counter = registry.counter(
            "test_labeled_counter",
            "Test counter with labels",
            labelnames=["method", "status"],
        )

        counter.labels(method="GET", status="200").inc()
        counter.labels(method="POST", status="201").inc(2)

        # Labels should work correctly
        assert counter.labels(method="GET", status="200")._value.get() == 1
        assert counter.labels(method="POST", status="201")._value.get() == 2

    def test_namespace_and_subsystem(self) -> None:
        """Test that namespace and subsystem create unique keys."""
        registry = MetricsRegistry(registry=CollectorRegistry())

        counter1 = registry.counter("requests", namespace="app1")
        counter2 = registry.counter("requests", namespace="app2")
        counter3 = registry.counter("requests", namespace="app1", subsystem="api")

        # Should all be different instances
        assert counter1 is not counter2
        assert counter1 is not counter3
        assert counter2 is not counter3

        # But retrieving with same parameters should return same instance
        counter1_again = registry.counter("requests", namespace="app1")
        assert counter1 is counter1_again

    def test_histogram_with_custom_buckets(self) -> None:
        """Test that histograms can be created with custom buckets."""
        registry = MetricsRegistry(registry=CollectorRegistry())

        buckets = [0.1, 0.5, 1.0, 5.0]
        histogram = registry.histogram(
            "test_custom_histogram",
            "Test histogram with custom buckets",
            buckets=buckets,
        )

        # Should be usable
        histogram.observe(0.3)
        assert histogram._count.get() == 1

    def test_clear(self) -> None:
        """Test that clear() removes all cached metrics."""
        registry = MetricsRegistry(registry=CollectorRegistry())

        counter1 = registry.counter("test_counter")
        gauge1 = registry.gauge("test_gauge")

        registry.clear()

        # After clearing, should get new instances
        counter2 = registry.counter("test_counter")
        gauge2 = registry.gauge("test_gauge")

        assert counter1 is not counter2
        assert gauge1 is not gauge2

    def test_default_registry(self) -> None:
        """Test that the default global registry works."""
        registry1 = get_default_metrics_registry()
        registry2 = get_default_metrics_registry()

        # Should return the same instance
        assert registry1 is registry2

    def test_multiple_independent_registries(self) -> None:
        """Test that multiple MetricsRegistry instances are independent."""
        registry1 = MetricsRegistry(registry=CollectorRegistry())
        registry2 = MetricsRegistry(registry=CollectorRegistry())

        counter1 = registry1.counter("test_counter")
        counter2 = registry2.counter("test_counter")

        # Should be different instances
        assert counter1 is not counter2

        counter1.inc()

        # Should not affect counter2
        assert counter1._value.get() == 1
        assert counter2._value.get() == 0


class TestMetricDecorators:
    """Test suite for metric decorators."""

    def test_count_calls_decorator(self) -> None:
        """Test that count_calls decorator counts function calls."""
        custom_registry = CollectorRegistry()
        metrics = MetricsRegistry(registry=custom_registry)

        @count_calls("test_function_calls", registry=metrics)
        def test_function(x: int) -> int:
            return x * 2

        # Call the function a few times
        test_function(1)
        test_function(2)
        test_function(3)

        # Check that counter was incremented
        counter = metrics.counter("test_function_calls")
        assert counter._value.get() == 3

    def test_count_calls_with_default_name(self) -> None:
        """Test that count_calls uses function name if no metric name provided."""
        custom_registry = CollectorRegistry()
        metrics = MetricsRegistry(registry=custom_registry)

        @count_calls(registry=metrics)
        def my_function() -> str:
            return "hello"

        my_function()
        my_function()

        # Should create counter with function name + _calls_total
        counter = metrics.counter("my_function_calls_total")
        assert counter._value.get() == 2

    def test_count_calls_with_labels(self) -> None:
        """Test that count_calls decorator works with labels."""
        custom_registry = CollectorRegistry()
        metrics = MetricsRegistry(registry=custom_registry)

        @count_calls("labeled_function", registry=metrics, labels={"method": "POST"})
        def test_function() -> None:
            pass

        test_function()
        test_function()

        counter = metrics.counter("labeled_function")
        assert counter.labels(method="POST")._value.get() == 2

    def test_time_calls_decorator(self) -> None:
        """Test that time_calls decorator records execution time."""
        custom_registry = CollectorRegistry()
        metrics = MetricsRegistry(registry=custom_registry)

        @time_calls("test_function_duration", registry=metrics)
        def slow_function() -> None:
            time.sleep(0.01)

        slow_function()
        slow_function()

        # Check that histogram recorded observations
        histogram = metrics.histogram("test_function_duration")
        assert histogram._count.get() == 2

    def test_time_calls_with_summary(self) -> None:
        """Test that time_calls can use Summary instead of Histogram."""
        custom_registry = CollectorRegistry()
        metrics = MetricsRegistry(registry=custom_registry)

        @time_calls("test_summary_duration", registry=metrics, use_histogram=False)
        def test_function() -> None:
            time.sleep(0.01)

        test_function()

        # Check that summary recorded observations
        summary = metrics.summary("test_summary_duration")
        assert summary._count.get() == 1

    def test_time_calls_with_custom_buckets(self) -> None:
        """Test that time_calls accepts custom buckets."""
        custom_registry = CollectorRegistry()
        metrics = MetricsRegistry(registry=custom_registry)

        @time_calls("test_buckets", registry=metrics, buckets=[0.01, 0.05, 0.1])
        def test_function() -> None:
            time.sleep(0.005)

        test_function()

        histogram = metrics.histogram("test_buckets")
        assert histogram._count.get() == 1

    def test_count_and_time_decorator(self) -> None:
        """Test that count_and_time decorator both counts and times."""
        custom_registry = CollectorRegistry()
        metrics = MetricsRegistry(registry=custom_registry)

        @count_and_time("combined_metric", registry=metrics)
        def test_function(x: int) -> int:
            time.sleep(0.01)
            return x * 2

        test_function(5)
        test_function(10)

        # Check counter
        counter = metrics.counter("combined_metric_calls_total")
        assert counter._value.get() == 2

        # Check histogram
        histogram = metrics.histogram("combined_metric_duration_seconds")
        assert histogram._count.get() == 2

    @pytest.mark.asyncio
    async def test_count_calls_async(self) -> None:
        """Test that count_calls works with async functions."""
        custom_registry = CollectorRegistry()
        metrics = MetricsRegistry(registry=custom_registry)

        @count_calls("async_function_calls", registry=metrics)
        async def async_function() -> str:
            await asyncio.sleep(0.01)
            return "done"

        await async_function()
        await async_function()

        counter = metrics.counter("async_function_calls")
        assert counter._value.get() == 2

    @pytest.mark.asyncio
    async def test_time_calls_async(self) -> None:
        """Test that time_calls works with async functions."""
        custom_registry = CollectorRegistry()
        metrics = MetricsRegistry(registry=custom_registry)

        @time_calls("async_duration", registry=metrics)
        async def async_function() -> None:
            await asyncio.sleep(0.01)

        await async_function()
        await async_function()

        histogram = metrics.histogram("async_duration")
        assert histogram._count.get() == 2

    @pytest.mark.asyncio
    async def test_count_and_time_async(self) -> None:
        """Test that count_and_time works with async functions."""
        custom_registry = CollectorRegistry()
        metrics = MetricsRegistry(registry=custom_registry)

        @count_and_time("async_combined", registry=metrics)
        async def async_function() -> int:
            await asyncio.sleep(0.01)
            return 42

        result = await async_function()
        assert result == 42

        counter = metrics.counter("async_combined_calls_total")
        assert counter._value.get() == 1

        histogram = metrics.histogram("async_combined_duration_seconds")
        assert histogram._count.get() == 1

    def test_decorators_preserve_function_metadata(self) -> None:
        """Test that decorators preserve function name and docstring."""

        @count_calls()
        def documented_function() -> None:
            """This is a docstring."""
            pass

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a docstring."

    def test_decorator_with_namespace_subsystem(self) -> None:
        """Test that decorators work with namespace and subsystem."""
        custom_registry = CollectorRegistry()
        metrics = MetricsRegistry(registry=custom_registry)

        @count_calls("requests", registry=metrics, namespace="myapp", subsystem="api")
        def handle_request() -> None:
            pass

        handle_request()

        # The metric should be created with namespace and subsystem
        counter = metrics.counter("requests", namespace="myapp", subsystem="api")
        assert counter._value.get() == 1
