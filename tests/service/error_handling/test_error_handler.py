
import pytest
from fastapi import HTTPException
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.service.error_handling.error_handler import ErrorHandler


class TestErrorHandler:
    """Test suite for ErrorHandler class."""

    def test_raise_error(self):
        """Test direct error raising."""
        with pytest.raises(HTTPException) as exc_info:
            ErrorHandler.raise_error("Test error")
        assert exc_info.value.status_code == HTTP_422_UNPROCESSABLE_ENTITY
        assert exc_info.value.detail == "Test error"

        # Test with custom status code
        with pytest.raises(HTTPException) as exc_info:
            ErrorHandler.raise_error("Not found", HTTP_404_NOT_FOUND)
        assert exc_info.value.status_code == HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Not found"

    def test_validate(self):
        """Test condition validation."""
        # Test passing validation
        ErrorHandler.validate(True, "Should not raise")  # Should not raise

        # Test failing validation
        with pytest.raises(HTTPException) as exc_info:
            ErrorHandler.validate(False, "Validation failed")
        assert exc_info.value.status_code == HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Validation failed"

        # Test with custom status code
        with pytest.raises(HTTPException) as exc_info:
            ErrorHandler.validate(False, "Not found", HTTP_404_NOT_FOUND)
        assert exc_info.value.status_code == HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Not found"

    def test_handle_exceptions_decorator(self):
        """Test exception handling decorator."""

        @ErrorHandler.handle_exceptions("Operation failed")
        def function_that_raises():
            raise ValueError("Something went wrong")

        @ErrorHandler.handle_exceptions("Operation failed")
        def function_that_raises_http():
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="Original HTTP exception"
            )

        @ErrorHandler.handle_exceptions("Operation failed")
        def function_that_succeeds():
            return "success"

        # Test handling of regular exception
        with pytest.raises(HTTPException) as exc_info:
            function_that_raises()
        assert exc_info.value.status_code == HTTP_422_UNPROCESSABLE_ENTITY
        assert exc_info.value.detail == "Operation failed: Something went wrong"

        # Test that HTTP exceptions are re-raised without modification
        with pytest.raises(HTTPException) as exc_info:
            function_that_raises_http()
        assert exc_info.value.status_code == HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Original HTTP exception"

        # Test successful execution
        assert function_that_succeeds() == "success"

    def test_handle_exceptions_with_custom_status(self):
        """Test exception handling decorator with custom status code."""

        @ErrorHandler.handle_exceptions("Not found", HTTP_404_NOT_FOUND)
        def function_that_raises():
            raise ValueError("Item not found")

        with pytest.raises(HTTPException) as exc_info:
            function_that_raises()
        assert exc_info.value.status_code == HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Not found: Item not found"

    def test_complex_validation_scenario(self):
        """Test more complex validation scenarios."""

        def complex_operation(value: int) -> str:
            """Example of combining multiple validations."""
            ErrorHandler.validate(
                isinstance(value, int), "Value must be an integer", HTTP_400_BAD_REQUEST
            )

            ErrorHandler.validate(
                value > 0, "Value must be positive", HTTP_400_BAD_REQUEST
            )

            if value > 100:
                ErrorHandler.raise_error(
                    "Value too large", HTTP_422_UNPROCESSABLE_ENTITY
                )

            return "Valid value"

        # Test valid input
        assert complex_operation(50) == "Valid value"

        # Test type validation
        with pytest.raises(HTTPException) as exc_info:
            complex_operation("not an int")  # type: ignore
        assert exc_info.value.status_code == HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Value must be an integer"

        # Test range validation
        with pytest.raises(HTTPException) as exc_info:
            complex_operation(-1)
        assert exc_info.value.status_code == HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Value must be positive"

        # Test upper limit
        with pytest.raises(HTTPException) as exc_info:
            complex_operation(101)
        assert exc_info.value.status_code == HTTP_422_UNPROCESSABLE_ENTITY
        assert exc_info.value.detail == "Value too large"
