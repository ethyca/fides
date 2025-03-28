"""Error handling utilities for the API.

-----------------------------------------------------------------------------
Example Usage
-----------------------------------------------------------------------------

# Example: Resource not found handling
@router.get("/items/{item_id}")
@ErrorHandler.handle_endpoint(
    error_message="Failed to retrieve item",
    resource_name="Item"  # Will raise ResourceNotFoundError if None is returned
)
async def get_item(item_id: str) -> Item:
    return await db.get_item(item_id)

# Example: Validation error handling
@router.post("/items")
@ErrorHandler.handle_endpoint(error_message="Failed to create item")
async def create_item(item: ItemCreate) -> Item:
    # Validate business rules
    ErrorHandler.validate(
        item.price > 0,
        "Price must be greater than 0",
        field="price"
    )
    return await db.create_item(item)

# Simple validation
ErrorHandler.validate(user.age >= 18, "Must be 18 or older")

# Validation with field
ErrorHandler.validate(
    len(password) >= 8,
    "Password too short",
    field="password"
)

# Custom error class
ErrorHandler.validate(
    user_exists,
    "User not found",
    error_class=ResourceNotFoundError
)

"""

import inspect
import traceback
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Awaitable, Callable, Optional, Type, TypeVar
from uuid import uuid4

from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from loguru import logger
from pydantic import BaseModel
from starlette.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_503_SERVICE_UNAVAILABLE,
)

T = TypeVar("T")
AsyncCallable = Callable[..., Awaitable[T]]

# -----------------------------------------------------------------------------
# Models and Types
# -----------------------------------------------------------------------------


class ErrorType(str, Enum):
    """Enum defining standard error types and their associated status codes."""

    AUTHENTICATION = "AUTHENTICATION_ERROR"
    AUTHORIZATION = "AUTHORIZATION_ERROR"
    CONFLICT = "CONFLICT_ERROR"
    INTERNAL = "INTERNAL_ERROR"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMIT = "RATE_LIMIT_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    UNPROCESSABLE_ENTITY = "UNPROCESSABLE_ENTITY"
    VALIDATION = "VALIDATION_ERROR"

    @property
    def status_code(self) -> int:
        """Get the HTTP status code for this error type."""
        return {
            ErrorType.VALIDATION: HTTP_400_BAD_REQUEST,
            ErrorType.AUTHENTICATION: HTTP_401_UNAUTHORIZED,
            ErrorType.AUTHORIZATION: HTTP_403_FORBIDDEN,
            ErrorType.NOT_FOUND: HTTP_404_NOT_FOUND,
            ErrorType.METHOD_NOT_ALLOWED: HTTP_405_METHOD_NOT_ALLOWED,
            ErrorType.CONFLICT: HTTP_409_CONFLICT,
            ErrorType.RATE_LIMIT: HTTP_429_TOO_MANY_REQUESTS,
            ErrorType.INTERNAL: HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorType.SERVICE_UNAVAILABLE: HTTP_503_SERVICE_UNAVAILABLE,
            ErrorType.UNPROCESSABLE_ENTITY: HTTP_422_UNPROCESSABLE_ENTITY,
        }[self]

    @property
    def category(self) -> str:
        """Get the error category for this error type."""
        if self in [ErrorType.AUTHENTICATION, ErrorType.AUTHORIZATION]:
            return "SECURITY_ERROR"
        if self == ErrorType.VALIDATION:
            return "VALIDATION_ERROR"
        if self.status_code >= 500:
            return "SERVER_ERROR"
        return "CLIENT_ERROR"

    def __str__(self) -> str:
        return self.value


class ErrorLocation(BaseModel):
    """Location information for where an error occurred."""

    file: str
    function: str
    line_number: int
    code_context: Optional[list[str]] = None


class ErrorContext(BaseModel):
    """Detailed context about the error occurrence."""

    timestamp: str  # Store as ISO format string
    trace_id: str
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    location: Optional[ErrorLocation] = None
    stack_trace: Optional[list[str]] = None


class ErrorDetail(BaseModel):
    """Enhanced error detail model with rich context."""

    message: str
    code: str
    field: Optional[str] = None
    details: Optional[dict[str, Any]] = None
    context: Optional[ErrorContext] = None


class ErrorResponse(BaseModel):
    """Enhanced error response with detailed context."""

    error: ErrorDetail
    request_id: str


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------


class FidesError(HTTPException):
    """Enhanced base exception class with rich context."""

    def __init__(
        self,
        detail: str,
        error_type: ErrorType,
        field: Optional[str] = None,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
        exc_info: Optional[Exception] = None,
        status_code: Optional[int] = None,
    ):
        self.error_type = error_type
        self.status_code = status_code or error_type.status_code
        self.field = field
        self.details = details

        # Create the error response
        self.error_response = ErrorHandler.get_error_response(
            message=detail,
            code=str(error_type),
            field=field,  # Ensure field is included
            details=details,  # Ensure details are included
            request=request,
            exc_info=exc_info,
        )

        # For HTTPException, we pass the serialized error response
        super().__init__(
            status_code=self.status_code,
            detail={"detail": jsonable_encoder(self.error_response.model_dump())},
        )


class ValidationError(FidesError):
    """Raised when validation fails."""

    def __init__(
        self,
        detail: str,
        field: Optional[str] = None,
        details: Optional[dict] = None,
        **kwargs: Any,
    ):
        super().__init__(
            detail=detail,
            error_type=ErrorType.VALIDATION,
            field=field,
            details=details,
            **kwargs,
        )


class ResourceNotFoundError(FidesError):
    """Raised when a requested resource is not found."""

    def __init__(self, detail: str, headers: Optional[dict] = None):
        super().__init__(
            detail=detail, error_type=ErrorType.NOT_FOUND, field=None, details=None
        )


# -----------------------------------------------------------------------------
# Core Error Handler
# -----------------------------------------------------------------------------


class ErrorHandler:
    """Enhanced error handling utility class."""

    @staticmethod
    def validate(
        condition: bool,
        detail: str,
        error_class: Type[FidesError] = ValidationError,
        **kwargs: Any,
    ) -> None:
        """Validate a condition and raise an error if it fails.

        Args:
            condition: The condition to validate
            detail: Error message if validation fails
            error_class: The error class to raise (default: ValidationError)
            **kwargs: Additional arguments to pass to the error class

        Raises:
            FidesError: If the condition is False
        """
        if not condition:
            raise error_class(detail=detail, **kwargs)

    @staticmethod
    def _is_relevant_frame(filename: str) -> bool:
        """Check if a frame is relevant for error location tracking.

        Args:
            filename: The filename to check

        Returns:
            bool: True if the frame should be included in error tracking
        """
        # Allow frames from test files
        if (
            "tests/" in filename or "test_" in filename
        ):  # or "error_handling" in filename:
            return True

        # Skip common library paths
        skip_patterns = {
            "site-packages/",
            "lib/python",
            "dist-packages/",
            "__pycache__",
            "starlette/",
            "fastapi/",
            "asyncio/",
            "uvicorn/",
            "click/",
            "typing_extensions.py",
            "_pytest/",
            "pluggy/",
        }

        # Allow frames that are not in the skip patterns
        return not any(pattern in filename for pattern in skip_patterns)

    @staticmethod
    def _get_context_lines(
        filename: str, line_number: int, context_size: int = 2
    ) -> list[str]:
        """Get the lines of code around a specific line number."""
        if not filename:
            return []
        try:
            with open(filename, encoding="utf-8") as f:
                lines = f.readlines()
                start = max(0, line_number - context_size)
                end = min(len(lines), line_number + context_size)
                return lines[start:end]
        except (FileNotFoundError, IOError):
            return []

    @staticmethod
    def _find_caller_frame() -> Optional[inspect.Traceback]:
        """Find the relevant caller frame in the stack."""
        try:
            frames = []
            frame = inspect.currentframe()

            # Build list of all frames
            while frame:
                frames.append(frame)
                frame = frame.f_back

            # Reverse frames to start from the oldest
            frames.reverse()

            # Find the first relevant frame
            fallback_frame = None
            for frame in frames:
                filename = frame.f_code.co_filename

                if ErrorHandler._is_relevant_frame(filename):
                    return inspect.getframeinfo(frame, context=3)

                # Save the first non-skipped frame as a fallback
                if fallback_frame is None:
                    fallback_frame = frame

            # Return the fallback frame if no relevant frame is found
            if fallback_frame:
                logger.warning("Using fallback frame.")
                return inspect.getframeinfo(fallback_frame, context=3)
            return None

        except Exception as e:
            logger.warning(f"Error finding caller frame: {e}")
            return None
        finally:
            # Clean up frame references
            while frames:
                frame = frames.pop()
                del frame

    @staticmethod
    def get_error_location() -> ErrorLocation:
        """Extract location information from the current stack frame."""
        caller = ErrorHandler._find_caller_frame()

        if caller is not None:
            filename = caller.filename
            function = caller.function
            line_number = caller.lineno

            context_lines = ErrorHandler._get_context_lines(
                filename=filename, line_number=line_number
            )

            return ErrorLocation(
                file=filename,
                function=function,
                line_number=line_number,
                code_context=context_lines,
            )

        return ErrorLocation(file="unknown", function="unknown", line_number=0)

    @staticmethod
    def get_error_response(
        message: str,
        code: str,
        field: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        request: Optional[Request] = None,
        exc_info: Optional[Exception] = None,
    ) -> ErrorResponse:
        """Create enhanced error response with context.

        Returns:
            ErrorResponse: Formatted error response with context
        """
        context = ErrorHandler._build_error_context(request, exc_info)
        return ErrorResponse(
            error=ErrorDetail(
                message=message,
                code=code,
                field=field,  # Ensure field is included
                details=details,  # Ensure details are included
                context=context,
            ),
            request_id=context.trace_id,
        )

    @staticmethod
    def safe_serialize(obj: Any) -> Any:
        """Safely serialize objects, replacing circular references and unserializable objects."""
        try:
            if isinstance(obj, dict):
                # Recursively process dictionaries
                return {
                    key: ErrorHandler.safe_serialize(value)
                    for key, value in obj.items()
                }
            if isinstance(obj, list):
                # Recursively process lists
                return [ErrorHandler.safe_serialize(item) for item in obj]
            if isinstance(obj, BaseModel):
                # Serialize Pydantic models
                return obj.dict()
            return jsonable_encoder(obj)
        except (TypeError, ValueError, RecursionError):
            # Replace unserializable objects with a placeholder
            return "[Unserializable Object]"

    @classmethod
    def _log_error(
        cls, error: Exception, func_name: str, args: tuple, kwargs: dict
    ) -> None:
        """Log error details using structured logging."""
        try:
            # Serialize the error detail safely
            error_detail = ErrorHandler.safe_serialize(
                getattr(error, "detail", str(error))
            )

            # Log the error with structured details
            logger.error(
                error_detail,
                exc_info=True,
                extra={
                    "function": func_name,
                    "args": ErrorHandler.safe_serialize(args),
                    "kwargs": ErrorHandler.safe_serialize(kwargs),
                },
            )
        except Exception as log_error:
            logger.warning(f"Failed to log error details: {log_error}")

    @staticmethod
    def _build_error_response(
        error: Exception, error_message: str, func_name: str, args: tuple, kwargs: dict
    ) -> JSONResponse:
        """Build a structured error response."""
        status_code = getattr(error, "detail", {}).get(
            "status_code", HTTP_500_INTERNAL_SERVER_ERROR
        )
        exception_message = getattr(error, "detail", {}).get("message", str(error))
        field = getattr(error, "field", None)  # Extract field if available
        details = getattr(error, "details", None)  # Extract details if available
        # Log the error
        ErrorHandler._log_error(error, func_name, args, kwargs)

        # Return a structured error response
        error_response = ErrorHandler.get_error_response(
            message=f"{error_message}: {exception_message}",
            code=ErrorType.INTERNAL,  # Default to INTERNAL error type
            field=field,  # Pass field explicitly
            details=ErrorHandler.safe_serialize(details),  # Serialize details safely
        )
        return JSONResponse(
            status_code=status_code,
            content={"detail": jsonable_encoder(error_response.dict())},
        )

    @staticmethod
    def _build_http_exception_response(
        http_exc: HTTPException, error_message: str
    ) -> JSONResponse:
        """Build a structured response for HTTP exceptions."""
        # Extract the exception details
        exception_message = (
            http_exc.detail if isinstance(http_exc.detail, str) else error_message
        )
        field = getattr(http_exc, "field", None)
        details = getattr(http_exc, "details", None)

        # Use the existing mapping to determine the error type
        error_type = ErrorType.METHOD_NOT_ALLOWED  # Default to METHOD_NOT_ALLOWED
        if hasattr(ErrorType, "status_code"):
            error_type = next(
                (
                    etype
                    for etype in ErrorType
                    if etype.status_code == http_exc.status_code
                ),
                ErrorType.INTERNAL,  # Fallback to INTERNAL if no match is found
            )

        # Build the error response
        error_response = ErrorHandler.get_error_response(
            message=exception_message,
            code=error_type,  # Use the dynamically determined error type
            field=field,  # Pass field explicitly
            details=ErrorHandler.safe_serialize(details),  # Serialize details safely
        )

        # Return the JSON response
        return JSONResponse(
            status_code=http_exc.status_code,
            content={
                "detail": jsonable_encoder(error_response.dict())
            },  # Ensure structured response
        )

    @staticmethod
    def _build_error_context(
        request: Optional[Request] = None,
        exc_info: Optional[Exception] = None,
    ) -> ErrorContext:
        """Builds error context with all available information."""
        logger.debug(exc_info)
        context = ErrorContext(
            timestamp=datetime.utcnow().isoformat(),  # Pre-serialize datetime
            trace_id=str(uuid4()),
            location=ErrorHandler.get_error_location(),
        )

        if request:
            context.request_path = str(request.url)
            context.request_method = request.method

        if exc_info:
            context.stack_trace = traceback.format_exception(
                type(exc_info), exc_info, exc_info.__traceback__
            )

        return context

    @classmethod
    def _handle_error(
        cls, error: Exception, error_message: str, request: Optional[Request]
    ) -> None:
        """Handle and raise appropriate error type."""
        if isinstance(error, (ValidationError, ResourceNotFoundError, HTTPException)):
            raise error

        raise FidesError(
            detail=f"{error_message}: {str(error)}",
            error_type=ErrorType.INTERNAL,
            request=request,
            exc_info=error,
        )

    @staticmethod
    def handle_endpoint(
        error_message: str,
        resource_name: Optional[str] = None,
    ) -> Callable[[AsyncCallable], AsyncCallable]:
        """Decorator to handle errors in endpoint functions."""

        def decorator(func: AsyncCallable) -> AsyncCallable:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    # Execute the wrapped function
                    result = await func(*args, **kwargs)

                    # Raise a ResourceNotFoundError if the resource is None
                    if resource_name and result is None:
                        raise ResourceNotFoundError(detail=f"{resource_name} not found")

                    return result  # type: ignore[no-any-return]

                except HTTPException as http_exc:
                    # Handle FastAPI HTTP exceptions
                    return ErrorHandler._build_http_exception_response(
                        http_exc, error_message
                    )

                except Exception as e:
                    # Handle all other exceptions
                    return ErrorHandler._build_error_response(
                        e, error_message, func.__name__, args, kwargs
                    )

            return wrapper

        return decorator
