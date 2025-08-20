"""Tests for the retry system in streaming storage."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from fides.api.service.storage.streaming.retry import (
    PermanentError,
    RetryableError,
    RetryConfig,
    TransientError,
    calculate_backoff_delay,
    is_s3_transient_error,
    is_transient_error,
    retry_cloud_storage_operation,
    retry_s3_operation,
    retry_with_backoff,
)


class TestRetryConfig:
    """Test RetryConfig class."""

    def test_retry_config_defaults(self):
        """Test RetryConfig with default values."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.backoff_factor == 2.0
        assert config.jitter is True

    def test_retry_config_custom_values(self):
        """Test RetryConfig with custom values."""
        config = RetryConfig(
            max_retries=5,
            base_delay=2.0,
            max_delay=120.0,
            backoff_factor=3.0,
            jitter=False,
        )
        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.backoff_factor == 3.0
        assert config.jitter is False


class TestErrorClassification:
    """Test error classification functions."""

    def test_is_transient_error_network_issues(self):
        """Test that network-related errors are classified as transient."""
        assert is_transient_error(Exception("Connection timeout"))
        assert is_transient_error(Exception("Network error"))
        assert is_transient_error(Exception("Service unavailable"))
        assert is_transient_error(Exception("Rate limit exceeded"))

    def test_is_transient_error_permanent_issues(self):
        """Test that permanent errors are not classified as transient."""
        assert not is_transient_error(Exception("Invalid configuration"))
        assert not is_transient_error(Exception("Permission denied"))
        assert not is_transient_error(Exception("File not found"))

    def test_is_s3_transient_error_aws_codes(self):
        """Test S3-specific transient error detection."""
        # Mock a boto3 ClientError
        mock_error = Mock()
        mock_error.response = {"Error": {"Code": "ThrottlingException"}}
        assert is_s3_transient_error(mock_error)

        mock_error.response = {"Error": {"Code": "SlowDown"}}
        assert is_s3_transient_error(mock_error)

    def test_is_s3_transient_error_non_aws(self):
        """Test S3 transient error detection with non-AWS errors."""
        # Non-AWS error should fall back to generic detection
        assert is_s3_transient_error(Exception("Connection timeout"))
        assert not is_s3_transient_error(Exception("Invalid configuration"))


class TestBackoffCalculation:
    """Test exponential backoff delay calculation."""

    def test_calculate_backoff_delay_basic(self):
        """Test basic exponential backoff calculation."""
        delay = calculate_backoff_delay(1, 1.0, 60.0, 2.0, jitter=False)
        assert delay == 1.0

        delay = calculate_backoff_delay(2, 1.0, 60.0, 2.0, jitter=False)
        assert delay == 2.0

        delay = calculate_backoff_delay(3, 1.0, 60.0, 2.0, jitter=False)
        assert delay == 4.0

    def test_calculate_backoff_delay_max_cap(self):
        """Test that delay is capped at maximum value."""
        delay = calculate_backoff_delay(10, 1.0, 10.0, 2.0, jitter=False)
        assert delay == 10.0

    def test_calculate_backoff_delay_zero_attempt(self):
        """Test that zero attempt returns zero delay."""
        delay = calculate_backoff_delay(0, 1.0, 60.0, 2.0, jitter=False)
        assert delay == 0


class TestRetryDecorators:
    """Test retry decorators."""

    @patch("time.sleep")
    def test_retry_with_backoff_success_first_try(self, mock_sleep):
        """Test retry decorator when function succeeds on first try."""

        @retry_with_backoff()
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"
        mock_sleep.assert_not_called()

    @patch("time.sleep")
    def test_retry_with_backoff_success_after_retry(self, mock_sleep):
        """Test retry decorator when function succeeds after retry."""
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.1)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TransientError("Temporary failure")
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 2
        mock_sleep.assert_called_once()

    @patch("time.sleep")
    def test_retry_with_backoff_max_retries_exceeded(self, mock_sleep):
        """Test retry decorator when max retries are exceeded."""

        @retry_with_backoff(max_retries=2, base_delay=0.1)
        def test_func():
            raise TransientError("Always fails")

        with pytest.raises(TransientError, match="Always fails"):
            test_func()

        # Should have slept twice (for retries 1 and 2)
        assert mock_sleep.call_count == 2

    @patch("time.sleep")
    def test_retry_with_backoff_permanent_error(self, mock_sleep):
        """Test retry decorator with permanent error (no retry)."""

        @retry_with_backoff(max_retries=3, base_delay=0.1)
        def test_func():
            raise PermanentError("Configuration error")

        with pytest.raises(PermanentError, match="Configuration error"):
            test_func()

        # Should not sleep for permanent errors
        mock_sleep.assert_not_called()

    def test_retry_s3_operation_decorator(self):
        """Test S3-specific retry decorator."""

        @retry_s3_operation("test operation")
        def test_func():
            return "s3 success"

        result = test_func()
        assert result == "s3 success"

    def test_retry_cloud_storage_operation_decorator(self):
        """Test cloud-agnostic retry decorator."""

        @retry_cloud_storage_operation("test provider", "test operation")
        def test_func():
            return "cloud success"

        result = test_func()
        assert result == "cloud success"


class TestRetryIntegration:
    """Test integration of retry system with actual operations."""

    @patch("time.sleep")
    def test_retry_with_transient_errors(self, mock_sleep):
        """Test retry system with transient errors."""
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.1)
        def download_operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Connection timeout")
            elif call_count == 2:
                raise Exception("Rate limit exceeded")
            return "download successful"

        # Should succeed on third attempt
        result = download_operation()
        assert result == "download successful"
        assert call_count == 3
        assert mock_sleep.call_count == 2

    def test_retry_config_from_settings(self):
        """Test creating retry config from application settings."""
        with patch(
            "fides.api.config.execution_settings.get_settings"
        ) as mock_get_settings:
            mock_settings = Mock()
            mock_settings.task_retry_count = 5
            mock_settings.task_retry_delay = 2
            mock_settings.task_retry_backoff = 3
            mock_get_settings.return_value = mock_settings

            from fides.api.service.storage.streaming.retry import (
                create_retry_config_from_settings,
            )

            config = create_retry_config_from_settings()

            assert config.max_retries == 5
            assert config.base_delay == 2
            assert config.backoff_factor == 3
            assert config.max_delay == 60.0
            assert config.jitter is True
