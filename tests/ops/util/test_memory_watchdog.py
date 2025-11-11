"""
Tests for memory watchdog utilities.

The memory watchdog provides proactive memory monitoring to prevent OOM kills
in Celery tasks by gracefully terminating when memory usage is high.
"""

import gc
import os
import signal
import threading
import time
from unittest.mock import MagicMock, Mock, patch

import pytest

from fides.api.models.application_config import ApplicationConfig
from fides.api.util.memory_watchdog import (
    MemoryLimitExceeded,
    MemoryWatchdog,
    _capture_heap_dump,
    _cgroup_memory_percent,
    _system_memory_percent,
    get_memory_watchdog_enabled,
    memory_limiter,
)


class TestGetMemoryWatchdogEnabled:
    """Test the get_memory_watchdog_enabled configuration function."""

    def test_default_setting_is_false(self, db):
        """Test that memory_watchdog_enabled defaults to False for backward compatibility."""
        # Clear any existing configuration first
        db.query(ApplicationConfig).delete()
        db.commit()

        # Verify default setting without any configuration
        result = get_memory_watchdog_enabled()
        assert (
            result is False
        ), "Memory watchdog should default to False for backward compatibility"

    def test_enabled_when_config_is_true(self, db):
        """Test that get_memory_watchdog_enabled returns True when configured."""
        # Set up application config with memory_watchdog_enabled = True
        config = ApplicationConfig(
            api_set={"execution": {"memory_watchdog_enabled": True}}
        )
        db.add(config)
        db.commit()

        result = get_memory_watchdog_enabled()
        assert (
            result is True
        ), "Should return True when memory_watchdog_enabled is configured as True"

    def test_disabled_when_config_is_false(self, db):
        """Test that get_memory_watchdog_enabled returns False when explicitly disabled."""
        # Set up application config with memory_watchdog_enabled = False
        config = ApplicationConfig(
            api_set={"execution": {"memory_watchdog_enabled": False}}
        )
        db.add(config)
        db.commit()

        result = get_memory_watchdog_enabled()
        assert (
            result is False
        ), "Should return False when memory_watchdog_enabled is configured as False"

    def test_exception_handling_returns_false(self):
        """Test that exceptions in config access return False (default)."""
        with patch("fides.api.api.deps.get_autoclose_db_session") as mock_get_db:
            mock_get_db.side_effect = Exception("Database error")

            result = get_memory_watchdog_enabled()
            assert result is False, "Should return False when config access fails"


class TestMemoryWatchdog:
    """Test the MemoryWatchdog class."""

    def test_initialization_defaults(self):
        """Test MemoryWatchdog initializes with correct defaults."""
        watchdog = MemoryWatchdog()

        assert watchdog.threshold == 90, "Default threshold should be 90%"
        assert (
            watchdog.check_interval == 0.5
        ), "Default check interval should be 0.5 seconds"
        assert watchdog.grace_period == 0, "Default grace period should be 0"
        assert watchdog._thread is None, "Thread should be None before starting"
        assert (
            not watchdog._monitoring.is_set()
        ), "Monitoring event should not be set initially"

    def test_initialization_custom_values(self):
        """Test MemoryWatchdog initializes with custom values."""
        watchdog = MemoryWatchdog(threshold=85, check_interval=1.0, grace_period=5)

        assert watchdog.threshold == 85
        assert watchdog.check_interval == 1.0
        assert watchdog.grace_period == 5

    @patch("fides.api.util.memory_watchdog._system_memory_percent")
    def test_start_and_stop(self, mock_memory_percent):
        """Test starting and stopping the watchdog."""
        mock_memory_percent.return_value = 50.0  # Low memory usage

        watchdog = MemoryWatchdog(check_interval=0.1)

        # Test start
        watchdog.start()
        assert watchdog._monitoring.is_set(), "Monitoring should be active after start"
        assert watchdog._thread is not None, "Thread should be created"
        assert watchdog._thread.is_alive(), "Thread should be running"

        # Test stop
        watchdog.stop()
        assert not watchdog._monitoring.is_set(), "Monitoring should be stopped"

        # Give thread time to stop
        time.sleep(0.2)
        assert not watchdog._thread.is_alive(), "Thread should be stopped"

    def test_context_manager(self):
        """Test MemoryWatchdog as context manager."""
        with patch(
            "fides.api.util.memory_watchdog._system_memory_percent"
        ) as mock_memory_percent:
            mock_memory_percent.return_value = 50.0

            watchdog = MemoryWatchdog(check_interval=0.1)

            with watchdog:
                assert (
                    watchdog._monitoring.is_set()
                ), "Should start monitoring in context"
                assert watchdog._thread is not None, "Thread should exist in context"

            time.sleep(0.2)  # Give thread time to stop
            assert (
                not watchdog._monitoring.is_set()
            ), "Should stop monitoring after context"

    @patch("fides.api.util.memory_watchdog.os.kill")
    @patch("fides.api.util.memory_watchdog._system_memory_percent")
    def test_memory_threshold_exceeded(self, mock_memory_percent, mock_kill):
        """Test watchdog triggers when memory threshold is exceeded."""
        mock_memory_percent.return_value = 95.0  # High memory usage

        watchdog = MemoryWatchdog(threshold=90, check_interval=0.1)

        watchdog.start()
        time.sleep(0.3)  # Give watchdog time to check memory

        # Verify SIGUSR1 signal was sent
        mock_kill.assert_called_with(os.getpid(), signal.SIGUSR1)

        watchdog.stop()

    def test_signal_handler_raises_exception(self):
        """Test that signal handler raises MemoryLimitExceeded."""
        with patch(
            "fides.api.util.memory_watchdog._system_memory_percent"
        ) as mock_memory_percent:
            mock_memory_percent.return_value = 95.0

            watchdog = MemoryWatchdog()

            # Test signal handler directly
            with pytest.raises(MemoryLimitExceeded) as exc_info:
                watchdog._signal_handler(signal.SIGUSR1, None)

            assert exc_info.value.memory_percent == 95.0
            assert "Memory usage exceeded threshold" in str(exc_info.value)


class TestMemoryLimiterDecorator:
    """Test the memory_limiter decorator."""

    def test_decorator_without_arguments(self, db):
        """Test memory_limiter decorator used without arguments."""
        # Setup config to disable watchdog
        config = ApplicationConfig(
            api_set={"execution": {"memory_watchdog_enabled": False}}
        )
        db.add(config)
        db.commit()

        @memory_limiter
        def test_function():
            return "success"

        result = test_function()
        assert (
            result == "success"
        ), "Function should execute normally when watchdog is disabled"

    def test_decorator_with_arguments(self, db):
        """Test memory_limiter decorator used with arguments."""
        # Setup config to disable watchdog
        config = ApplicationConfig(
            api_set={"execution": {"memory_watchdog_enabled": False}}
        )
        db.add(config)
        db.commit()

        @memory_limiter(threshold=85, check_interval=1.0)
        def test_function():
            return "success"

        result = test_function()
        assert (
            result == "success"
        ), "Function should execute normally when watchdog is disabled"

    @patch("fides.api.util.memory_watchdog.MemoryWatchdog")
    def test_decorator_when_enabled(self, mock_watchdog_class, db):
        """Test memory_limiter decorator when watchdog is enabled."""
        # Setup config to enable watchdog
        config = ApplicationConfig(
            api_set={"execution": {"memory_watchdog_enabled": True}}
        )
        db.add(config)
        db.commit()

        # Mock the watchdog instance
        mock_watchdog = Mock()
        mock_watchdog_class.return_value = mock_watchdog

        @memory_limiter(threshold=85)
        def test_function():
            return "success"

        result = test_function()

        # Verify watchdog was created with correct parameters
        mock_watchdog_class.assert_called_once_with(
            threshold=85, check_interval=0.5, grace_period=0
        )

        # Verify watchdog lifecycle
        mock_watchdog.start.assert_called_once()
        mock_watchdog.stop.assert_called_once()

        assert result == "success"

    @patch("fides.api.util.memory_watchdog.MemoryWatchdog")
    def test_decorator_when_disabled_by_config(self, mock_watchdog_class, db):
        """Test that decorator skips watchdog when disabled by configuration."""
        # Setup config to disable watchdog
        config = ApplicationConfig(
            api_set={"execution": {"memory_watchdog_enabled": False}}
        )
        db.add(config)
        db.commit()

        @memory_limiter(threshold=85)
        def test_function():
            return "success"

        result = test_function()

        # Verify watchdog was never created
        mock_watchdog_class.assert_not_called()
        assert result == "success"

    @patch("fides.api.util.memory_watchdog.MemoryWatchdog")
    def test_decorator_handles_memory_limit_exceeded(self, mock_watchdog_class, db):
        """Test decorator properly handles MemoryLimitExceeded exception."""
        # Setup config to enable watchdog
        config = ApplicationConfig(
            api_set={"execution": {"memory_watchdog_enabled": True}}
        )
        db.add(config)
        db.commit()

        # Mock the watchdog to raise MemoryLimitExceeded
        mock_watchdog = Mock()
        mock_watchdog_class.return_value = mock_watchdog

        @memory_limiter()
        def test_function():
            raise MemoryLimitExceeded("Memory exceeded", memory_percent=95.0)

        with pytest.raises(MemoryLimitExceeded) as exc_info:
            test_function()

        assert exc_info.value.memory_percent == 95.0

        # Verify watchdog lifecycle even with exception
        mock_watchdog.start.assert_called_once()
        mock_watchdog.stop.assert_called_once()

    @patch("fides.api.util.memory_watchdog.MemoryWatchdog")
    def test_decorator_cleanup_on_other_exceptions(self, mock_watchdog_class, db):
        """Test decorator ensures watchdog cleanup on other exceptions."""
        # Setup config to enable watchdog
        config = ApplicationConfig(
            api_set={"execution": {"memory_watchdog_enabled": True}}
        )
        db.add(config)
        db.commit()

        mock_watchdog = Mock()
        mock_watchdog_class.return_value = mock_watchdog

        @memory_limiter()
        def test_function():
            raise ValueError("Some other error")

        with pytest.raises(ValueError):
            test_function()

        # Verify watchdog cleanup even with other exceptions
        mock_watchdog.start.assert_called_once()
        mock_watchdog.stop.assert_called_once()


class TestMemoryPercentageCalculation:
    """Test memory percentage calculation functions."""

    @patch("builtins.open")
    def test_cgroup_memory_percent_v2(self, mock_open):
        """Test cgroup v2 memory percentage calculation."""
        # Mock cgroup v2 files
        mock_files = {
            "/sys/fs/cgroup/memory.current": "1073741824",  # 1GB used
            "/sys/fs/cgroup/memory.max": "2147483648",  # 2GB limit
        }

        def mock_open_side_effect(path, *args, **kwargs):
            if path in mock_files:
                mock_file = Mock()
                mock_file.read.return_value = mock_files[path]
                mock_file.__enter__ = Mock(return_value=mock_file)
                mock_file.__exit__ = Mock(return_value=None)
                return mock_file
            raise FileNotFoundError()

        mock_open.side_effect = mock_open_side_effect

        result = _cgroup_memory_percent()
        assert result == 50.0, "Should calculate 50% usage (1GB / 2GB)"

    @patch("builtins.open")
    def test_cgroup_memory_percent_v1(self, mock_open):
        """Test cgroup v1 memory percentage calculation."""
        # Mock cgroup v1 files (v2 files don't exist)
        mock_files = {
            "/sys/fs/cgroup/memory/memory.usage_in_bytes": "536870912",  # 512MB used
            "/sys/fs/cgroup/memory/memory.limit_in_bytes": "1073741824",  # 1GB limit
        }

        def mock_open_side_effect(path, *args, **kwargs):
            if path in mock_files:
                mock_file = Mock()
                mock_file.read.return_value = mock_files[path]
                mock_file.__enter__ = Mock(return_value=mock_file)
                mock_file.__exit__ = Mock(return_value=None)
                return mock_file
            raise FileNotFoundError()

        mock_open.side_effect = mock_open_side_effect

        result = _cgroup_memory_percent()
        assert result == 50.0, "Should calculate 50% usage (512MB / 1GB)"

    @patch("builtins.open")
    def test_cgroup_memory_percent_unlimited(self, mock_open):
        """Test cgroup memory percentage when limit is unlimited."""
        # Mock unlimited memory limit
        mock_files = {
            "/sys/fs/cgroup/memory.current": "1073741824",
            "/sys/fs/cgroup/memory.max": "max",  # Unlimited
        }

        def mock_open_side_effect(path, *args, **kwargs):
            if path in mock_files:
                mock_file = Mock()
                mock_file.read.return_value = mock_files[path]
                mock_file.__enter__ = Mock(return_value=mock_file)
                mock_file.__exit__ = Mock(return_value=None)
                return mock_file
            raise FileNotFoundError()

        mock_open.side_effect = mock_open_side_effect

        result = _cgroup_memory_percent()
        assert result is None, "Should return None for unlimited memory"

    @patch("builtins.open")
    def test_cgroup_memory_percent_no_files(self, mock_open):
        """Test cgroup memory percentage when files don't exist."""
        mock_open.side_effect = FileNotFoundError()

        result = _cgroup_memory_percent()
        assert result is None, "Should return None when cgroup files don't exist"

    @patch("fides.api.util.memory_watchdog._cgroup_memory_percent")
    @patch("fides.api.util.memory_watchdog.psutil.virtual_memory")
    def test_system_memory_percent_with_cgroup(self, mock_psutil, mock_cgroup):
        """Test system memory percentage prefers cgroup when available."""
        mock_cgroup.return_value = 75.0
        mock_psutil.return_value.percent = 60.0

        result = _system_memory_percent()
        assert result == 75.0, "Should use cgroup percentage when available"
        mock_psutil.assert_not_called()

    @patch("fides.api.util.memory_watchdog._cgroup_memory_percent")
    @patch("fides.api.util.memory_watchdog.psutil.virtual_memory")
    def test_system_memory_percent_fallback_to_psutil(self, mock_psutil, mock_cgroup):
        """Test system memory percentage falls back to psutil when cgroup unavailable."""
        mock_cgroup.return_value = None
        mock_psutil.return_value.percent = 60.0

        result = _system_memory_percent()
        assert result == 60.0, "Should fall back to psutil when cgroup unavailable"
        mock_psutil.assert_called_once()


class TestMemoryLimitExceeded:
    """Test the MemoryLimitExceeded exception."""

    def test_exception_with_memory_percent(self):
        """Test MemoryLimitExceeded exception with memory percentage."""
        exc = MemoryLimitExceeded("Memory exceeded", memory_percent=85.5)

        assert str(exc) == "Memory exceeded"
        assert exc.memory_percent == 85.5

    def test_exception_without_memory_percent(self):
        """Test MemoryLimitExceeded exception without memory percentage."""
        exc = MemoryLimitExceeded("Memory exceeded")

        assert str(exc) == "Memory exceeded"
        assert exc.memory_percent is None


class TestHeapDumpFunctionality:
    """Test heap dump and memory profiling capabilities."""

    @patch("fides.api.util.memory_watchdog.gc.get_count")
    @patch("fides.api.util.memory_watchdog.gc.get_objects")
    @patch("fides.api.util.memory_watchdog.gc.garbage", [])
    @patch("fides.api.util.memory_watchdog.objgraph.most_common_types")
    @patch("fides.api.util.memory_watchdog.psutil.Process")
    @patch("fides.api.util.memory_watchdog.logger")
    def test_capture_heap_dump_single_log_message(
        self, mock_logger, mock_process, mock_objgraph, mock_get_objects, mock_get_count
    ):
        """Test that capture_heap_dump logs entire report as a single message."""
        # Mock process memory info
        mock_mem_info = Mock()
        mock_mem_info.rss = 1024 * 1024 * 512  # 512 MiB
        mock_mem_info.vms = 1024 * 1024 * 1024  # 1024 MiB
        mock_process.return_value.memory_info.return_value = mock_mem_info

        # Mock objgraph
        mock_objgraph.return_value = [
            ("dict", 1000),
            ("list", 500),
            ("str", 300),
        ]

        # Mock gc stats
        mock_get_count.return_value = (100, 10, 1)
        mock_get_objects.return_value = list(range(5000))

        _capture_heap_dump()

        # Verify logger.error was called exactly ONCE with the full report
        assert (
            mock_logger.error.call_count == 1
        ), "Should log entire report as single message"

        # Get the logged message
        logged_message = str(mock_logger.error.call_args[0][0])

        # Verify all expected sections are in the single message
        assert "MEMORY DUMP - THRESHOLD EXCEEDED" in logged_message
        assert "PROCESS MEMORY STATS" in logged_message
        assert "RSS (Resident Set Size)" in logged_message
        assert "512.0 MiB" in logged_message
        assert "OBJECT TYPE COUNTS" in logged_message
        assert "GARBAGE COLLECTOR STATS" in logged_message
        assert "END OF MEMORY DUMP" in logged_message
        assert "dict" in logged_message
        assert "1,000" in logged_message
        assert "No uncollectable objects detected" in logged_message

    @patch("fides.api.util.memory_watchdog.objgraph.most_common_types")
    @patch("fides.api.util.memory_watchdog.logger")
    def test_capture_heap_dump_handles_exceptions(self, mock_logger, mock_objgraph):
        """Test that capture_heap_dump handles exceptions gracefully."""
        # Make objgraph raise an exception
        mock_objgraph.side_effect = Exception("Objgraph error")

        # _capture_heap_dump should handle the exception internally and not raise
        _capture_heap_dump()

        # Verify exception was logged
        mock_logger.exception.assert_called()

    @patch("fides.api.util.memory_watchdog.gc.collect")
    @patch("fides.api.util.memory_watchdog.objgraph.most_common_types")
    @patch("fides.api.util.memory_watchdog.logger")
    def test_capture_heap_dump_aligned_columns(
        self, mock_logger, mock_objgraph, mock_gc_collect
    ):
        """Test that object counts are aligned for readability."""
        mock_objgraph.return_value = [
            ("dict", 1000),
            ("list", 500),
            ("very_long_type_name", 123),
        ]

        _capture_heap_dump()

        logged_message = str(mock_logger.error.call_args[0][0])

        # Verify counts are formatted with commas and right-aligned
        assert "1,000" in logged_message
        assert "500" in logged_message
        assert "123" in logged_message
        # Verify gc.collect was called
        mock_gc_collect.assert_called_once()

    @patch("fides.api.util.memory_watchdog._capture_heap_dump")
    @patch("fides.api.util.memory_watchdog._system_memory_percent")
    def test_heap_dump_called_on_memory_exceeded(
        self, mock_memory_percent, mock_capture_heap_dump
    ):
        """Test that heap dump is captured when memory threshold is exceeded."""
        mock_memory_percent.return_value = 95.0

        watchdog = MemoryWatchdog()

        # Test signal handler directly
        with pytest.raises(MemoryLimitExceeded):
            watchdog._signal_handler(signal.SIGUSR1, None)

        # Verify heap dump was captured before exception was raised
        mock_capture_heap_dump.assert_called_once()
