# pylint: disable=unnecessary-pass
from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable, Optional, Type

from loguru import logger

from fides.config import CONFIG


class RetryableError(Exception):
    """Base exception for errors that should trigger retries."""

    pass  # pragma: no cover


class TransientError(RetryableError):
    """Exception for transient errors that should be retried."""

    pass  # pragma: no cover


class PermanentError(RetryableError):
    """Exception for permanent errors that should not be retried."""

    pass  # pragma: no cover


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        retry_on_exceptions: Optional[tuple[Type[Exception], ...]] = None,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.retry_on_exceptions = retry_on_exceptions or (Exception,)


def is_transient_error(error: Exception) -> bool:
    """
    Determine if an error is transient and should be retried.

    This is a cloud-agnostic implementation that can be extended
    with provider-specific logic.
    """
    # Check if this is our custom TransientError
    if isinstance(error, TransientError):
        return True

    error_str = str(error).lower()

    # Common transient error patterns across cloud providers
    transient_patterns = [
        "timeout",
        "timed out",
        "connection",
        "network",
        "temporary",
        "throttling",
        "rate limit",
        "too many requests",
        "service unavailable",
        "internal server error",
        "bad gateway",
        "gateway timeout",
        "request timeout",
        "connection reset",
        "broken pipe",
    ]

    return any(pattern in error_str for pattern in transient_patterns)


def is_s3_transient_error(error: Exception) -> bool:
    """
    Determine if an S3-specific error is transient and should be retried.

    This leverages AWS-specific error codes for optimal retry behavior.
    """
    try:
        # Check if this is a boto3 ClientError with AWS error codes
        if hasattr(error, "response") and hasattr(error.response, "get"):
            error_code = error.response.get("Error", {}).get("Code", "")

            # S3 transient error codes that should be retried
            transient_codes = {
                "ThrottlingException",
                "RequestLimitExceeded",
                "SlowDown",
                "InternalError",
                "ServiceUnavailable",
                "RequestTimeout",
                "NetworkingError",
                "ConnectionError",
                "Http500Error",
                "Http502Error",
                "Http503Error",
                "Http504Error",
            }

            return error_code in transient_codes

    except (AttributeError, KeyError):
        pass

    # Fall back to generic transient error detection
    return is_transient_error(error)


def calculate_backoff_delay(
    attempt: int,
    base_delay: float,
    max_delay: float,
    backoff_factor: float,
    jitter: bool = True,
) -> float:
    """
    Calculate exponential backoff delay with optional jitter.

    Args:
        attempt: Current attempt number (0-based)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Multiplier for each attempt
        jitter: Whether to add random jitter to prevent thundering herd

    Returns:
        Delay in seconds before next retry
    """
    if attempt == 0:
        return 0

    # Exponential backoff: base_delay * (backoff_factor ^ attempt)
    delay = base_delay * (backoff_factor ** (attempt - 1))

    # Cap at maximum delay
    delay = min(delay, max_delay)

    # Add jitter to prevent multiple retries from synchronizing
    if jitter:
        import random

        jitter_amount = delay * 0.1  # 10% jitter
        delay += random.uniform(-jitter_amount, jitter_amount)
        delay = max(0, delay)  # Ensure non-negative

    return delay


def retry_with_backoff(
    retry_config: Optional[RetryConfig] = None,
    operation_name: str = "operation",
) -> Callable:
    """
    Decorator for retrying operations with exponential backoff.

    This is a cloud-agnostic retry mechanism that can be extended
    with provider-specific retry logic.

    Args:
        retry_config: Configuration for retry behavior
        operation_name: Name of the operation for logging

    Returns:
        Decorated function with retry logic
    """
    if retry_config is None:
        # Use default configuration from settings
        settings = CONFIG.execution
        retry_config = RetryConfig(
            max_retries=settings.task_retry_count,
            base_delay=settings.task_retry_delay,
            backoff_factor=settings.task_retry_backoff,
        )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None

            for attempt in range(retry_config.max_retries + 1):
                try:
                    # Track retry attempts
                    if attempt > 0:
                        logger.debug(
                            "Retry attempt {}/{} for {}",
                            attempt,
                            retry_config.max_retries,
                            operation_name,
                        )

                    return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    # Check if this is a permanent error that shouldn't be retried
                    if isinstance(e, PermanentError):
                        logger.error(
                            "Permanent error in {}: {}. Not retrying.",
                            operation_name,
                            e,
                        )
                        raise

                    # Check if we should retry this error
                    should_retry = (
                        attempt < retry_config.max_retries
                        and isinstance(e, retry_config.retry_on_exceptions)
                        and (is_transient_error(e) or is_s3_transient_error(e))
                    )

                    if not should_retry:
                        logger.error(
                            "Non-retryable error in {}: {}. Not retrying.",
                            operation_name,
                            e,
                        )
                        raise

                    # Calculate delay for next retry
                    delay = calculate_backoff_delay(
                        attempt + 1,
                        retry_config.base_delay,
                        retry_config.max_delay,
                        retry_config.backoff_factor,
                        retry_config.jitter,
                    )

                    logger.warning(
                        "Transient error in {} (attempt {}/{}): {}. "
                        "Retrying in {:.1f} seconds...",
                        operation_name,
                        attempt + 1,
                        retry_config.max_retries + 1,
                        e,
                        delay,
                    )

                    # Sleep before retry
                    time.sleep(delay)

            # If we get here, all retries were exhausted
            logger.error(
                "Operation {} failed after {} retry attempts. Last error: {}",
                operation_name,
                retry_config.max_retries,
                last_exception,
            )
            if last_exception is not None:
                raise last_exception

            raise RuntimeError(
                f"Operation {operation_name} failed after {retry_config.max_retries} retry attempts"
            )

        return wrapper

    return decorator


def retry_s3_operation(
    operation_name: str = "S3 operation",
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
) -> Callable:
    """
    S3-optimized retry decorator with AWS-specific error handling.

    This decorator provides optimal retry behavior for S3 operations
    while maintaining cloud-agnostic compatibility.

    Args:
        operation_name: Name of the S3 operation
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Multiplier for each attempt

    Returns:
        Decorated function with S3-optimized retry logic
    """
    retry_config = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        jitter=True,
    )

    return retry_with_backoff(retry_config=retry_config, operation_name=operation_name)


def retry_cloud_storage_operation(
    provider: str = "cloud storage",
    operation_name: str = "storage operation",
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
) -> Callable:
    """
    Cloud-agnostic retry decorator for storage operations.

    This decorator provides retry logic that works across different
    cloud storage providers while allowing provider-specific optimizations.

    Args:
        provider: Name of the cloud storage provider
        operation_name: Name of the storage operation
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Multiplier for each attempt

    Returns:
        Decorated function with cloud-agnostic retry logic
    """
    retry_config = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        jitter=True,
    )

    return retry_with_backoff(
        retry_config=retry_config, operation_name=f"{provider} {operation_name}"
    )


def create_retry_config_from_settings() -> RetryConfig:
    """
    Create a RetryConfig instance from application settings.

    Returns:
        RetryConfig configured with application defaults
    """
    settings = CONFIG.execution
    return RetryConfig(
        max_retries=settings.task_retry_count,
        base_delay=settings.task_retry_delay,
        backoff_factor=settings.task_retry_backoff,
        max_delay=60.0,  # Cap at 1 minute
        jitter=True,
    )
