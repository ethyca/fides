from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from fastapi import HTTPException
from loguru import logger
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_422_UNPROCESSABLE_ENTITY

T = TypeVar("T")


class ErrorHandler:
    """Utility class for handling errors consistently throughout the application."""

    @staticmethod
    def raise_error(
        detail: str,
        status_code: int = HTTP_422_UNPROCESSABLE_ENTITY,
        log_message: Optional[str] = None,
    ) -> None:
        """Raise an HTTPException with consistent logging.

        Args:
            detail: Error message to include in the HTTPException
            status_code: HTTP status code to use (default: 422)
            log_message: Optional message to log before raising the exception

        Raises:
            HTTPException: Always raised with the provided details
        """
        if log_message:
            logger.error(log_message)
        raise HTTPException(status_code=status_code, detail=detail)

    @staticmethod
    def validate(
        condition: bool,
        detail: str,
        status_code: int = HTTP_400_BAD_REQUEST,
        log_message: Optional[str] = None,
    ) -> None:
        """Validate a condition and raise an error if it's False.

        Args:
            condition: The condition to check
            detail: Error message if condition is False
            status_code: HTTP status code to use if condition is False
            log_message: Optional message to log before raising the exception

        Raises:
            HTTPException: If the condition is False
        """
        if not condition:
            ErrorHandler.raise_error(detail, status_code, log_message)

    @classmethod
    def handle_exceptions(
        cls, error_message: str, status_code: int = HTTP_422_UNPROCESSABLE_ENTITY
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """Decorator to handle exceptions consistently.

        Args:
            error_message: Base error message to use
            status_code: HTTP status code to use for unexpected errors

        Returns:
            Callable: The decorated function that handles exceptions

        Note:
            This decorator will catch specific exceptions and convert them to HTTPExceptions.
            HTTPExceptions are re-raised as is, while other exceptions are wrapped with
            additional context.
        """

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Optional[T]:
                try:
                    return func(*args, **kwargs)
                except HTTPException:
                    # Re-raise HTTP exceptions without modification
                    raise
                except (ValueError, TypeError, AttributeError, KeyError) as e:
                    # Handle common validation and data access errors
                    cls.raise_error(
                        f"{error_message}: {str(e)}",
                        status_code,
                        f"{error_message}: {e}",
                    )
                except Exception as e:  # pylint: disable=broad-except
                    # Log unexpected errors with full context but present a sanitized message
                    logger.error(
                        f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True
                    )
                    cls.raise_error(
                        f"{error_message}: An unexpected error occurred",
                        status_code,
                        f"{error_message}: Unexpected {type(e).__name__}",
                    )
                return None  # This line is never reached but satisfies the return type checker

            return wrapper  # type: ignore[return-value]

        return decorator
