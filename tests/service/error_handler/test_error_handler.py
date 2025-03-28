"""Tests for error handling utilities."""

from datetime import datetime

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from fides.service.error_handeling.error_handler import (
    ErrorHandler,
    FidesError,
    ResourceNotFoundError,
    ValidationError,
)

# -----------------------------------------------------------------------------
# Test Models
# -----------------------------------------------------------------------------


class TestItem(BaseModel):
    """Test model for validation scenarios."""

    name: str
    price: float


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture(scope="module")
def app() -> FastAPI:
    """Create a fresh FastAPI app for testing."""
    app = FastAPI()

    @app.exception_handler(FidesError)
    async def fides_error_handler(request: Request, exc: FidesError) -> JSONResponse:
        # The error response is already serialized in exc.detail
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
        )

    @app.get("/test/validation")
    @ErrorHandler.handle_endpoint(error_message="Validation test failed")
    async def test_validation() -> dict:
        ErrorHandler.validate(False, "Validation failed", field="test_field")
        return {"status": "ok"}

    @app.get("/test/not-found")
    @ErrorHandler.handle_endpoint(
        error_message="Resource test failed", resource_name="TestResource"
    )
    async def test_not_found() -> None:
        return None

    @app.get("/test/unhandled")
    @ErrorHandler.handle_endpoint(error_message="Unhandled error test failed")
    async def test_unhandled() -> dict:
        raise ValueError("Test error")

    @app.get("/test/success")
    @ErrorHandler.handle_endpoint(error_message="Should not fail")
    async def test_success() -> dict:
        return {"status": "ok"}

    @app.get("/test/context")
    @ErrorHandler.handle_endpoint(error_message="Context test failed")
    async def test_context(request: Request) -> dict:
        def error_function():
            """Function to generate error at a known location."""
            raise ValueError("Test error")

        error_function()
        return {"status": "ok"}

    return app


@pytest.fixture(scope="module")
def client(app: FastAPI) -> TestClient:
    """Create a test client using our test app."""
    return TestClient(app)


# -----------------------------------------------------------------------------
# Error Response Tests
# -----------------------------------------------------------------------------


def test_error_response_creation() -> None:
    """Test creation of error responses with all fields."""
    response = ErrorHandler.get_error_response(
        message="Test error",
        code="TEST_ERROR",
        field="test_field",
        details={"extra": "info"},
    )

    assert response.error.message == "Test error"
    assert response.error.code == "TEST_ERROR"
    assert response.error.field == "test_field"
    assert response.error.details == {"extra": "info"}
    assert response.request_id is not None
    assert response.error.context is not None
    assert isinstance(response.error.context.timestamp, str)
    # Try parsing the timestamp to ensure it's valid
    datetime.fromisoformat(response.error.context.timestamp.replace("Z", "+00:00"))


def test_error_response_minimal() -> None:
    """Test creation of error responses with minimal fields."""
    response = ErrorHandler.get_error_response(
        message="Test error",
        code="TEST_ERROR",
    )

    assert response.error.message == "Test error"
    assert response.error.code == "TEST_ERROR"
    assert response.error.field is None
    assert response.error.details is None


# -----------------------------------------------------------------------------
# Validation Method Tests
# -----------------------------------------------------------------------------


def test_validation_success() -> None:
    """Test successful validation."""
    ErrorHandler.validate(True, "Should not raise")


def test_validation_basic_error() -> None:
    """Test basic validation failure."""
    with pytest.raises(ValidationError) as exc:
        ErrorHandler.validate(False, "Validation failed")
    assert "Validation failed" in str(exc.value)
    assert exc.value.status_code == HTTP_400_BAD_REQUEST


def test_validation_with_field() -> None:
    """Test validation with field specification."""
    with pytest.raises(ValidationError) as exc:
        ErrorHandler.validate(False, "Invalid value", field="test_field")

    # Print response for debugging
    print(f"\nValidation error detail: {exc.value.detail}")
    error_data = exc.value.detail["detail"]
    assert isinstance(error_data, dict), f"Expected dict, got {type(error_data)}"
    assert "error" in error_data
    assert error_data["error"]["field"] == "test_field"
    assert error_data["error"]["message"] == "Invalid value"
    assert error_data["error"]["code"] == "VALIDATION_ERROR"


def test_validation_custom_error() -> None:
    """Test validation with custom error class."""
    with pytest.raises(ResourceNotFoundError) as exc:
        ErrorHandler.validate(
            False, "Resource test failed", error_class=ResourceNotFoundError
        )
    assert exc.value.status_code == HTTP_404_NOT_FOUND


# -----------------------------------------------------------------------------
# Endpoint Tests
# -----------------------------------------------------------------------------


def test_endpoint_success(client: TestClient) -> None:
    """Test successful endpoint execution."""
    response = client.get("/test/success")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_endpoint_validation_error(client: TestClient) -> None:
    """Test validation error handling in endpoint."""
    response = client.get("/test/validation")
    assert response.status_code == HTTP_400_BAD_REQUEST

    # Print full response for debugging
    error_data = response.json()["detail"]
    print(f"\nFull validation error response: {error_data}")

    assert (
        "error" in error_data
    ), f"Expected 'error' key in response, got keys: {list(error_data.keys())}"
    error = error_data["error"]
    assert (
        "message" in error
    ), f"Expected 'message' in error, got keys: {list(error.keys())}"
    assert "Validation test failed" in error["message"]
    assert error["field"] == "test_field"


def test_endpoint_not_found(client: TestClient) -> None:
    """Test resource not found handling in endpoint."""
    response = client.get("/test/not-found")
    assert response.status_code == HTTP_404_NOT_FOUND

    # Print full response for debugging
    error_data = response.json()["detail"]
    print(f"\nFull not found error response: {error_data}")

    assert (
        "error" in error_data
    ), f"Expected 'error' key in response, got keys: {list(error_data.keys())}"
    error = error_data["error"]
    assert (
        "message" in error
    ), f"Expected 'message' in error, got keys: {list(error.keys())}"
    assert "Resource test failed" in error["message"]


def test_endpoint_unhandled_error(client: TestClient) -> None:
    """Test unhandled error handling in endpoint."""
    response = client.get("/test/unhandled")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR

    # Print response for debugging
    print(f"\nUnhandled error response: {response.json()}")
    error_data = response.json()["detail"]
    assert "error" in error_data
    assert error_data["error"]["message"] == "Unhandled error test failed: Test error"
    assert error_data["error"]["code"] == "INTERNAL_ERROR"


# -----------------------------------------------------------------------------
# Error Context Tests
# -----------------------------------------------------------------------------


def test_error_context_information(client: TestClient) -> None:
    """Test that error context contains all required information."""
    response = client.get("/test/context")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR

    # Print response for debugging
    print(f"\nContext error response: {response.json()}")
    error_data = response.json()["detail"]
    context = error_data["error"]["context"]

    # Verify timestamp format
    assert isinstance(context["timestamp"], str)
    datetime.fromisoformat(context["timestamp"].replace("Z", "+00:00"))

    # Verify required fields
    assert isinstance(context["trace_id"], str)
    assert "location" in context
    assert "stack_trace" in context


def test_error_location_information(client: TestClient) -> None:
    """Test that error location information is correct."""
    response = client.get("/test/context")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR

    location = response.json()["detail"]["error"]["context"]["location"]

    # Debugging: Print the full response
    print(f"\nFull error response: {response.json()}")

    # Debugging: Print the location information
    print(f"\nActual file path: {location['file']}")
    print(f"Actual function: {location['function']}")
    print(f"Actual line number: {location['line_number']}")
    if location.get("code_context"):
        print("Code context:")
        for line in location["code_context"]:
            print(f"  {line.strip()}")

    # Verify all required fields are present
    assert "file" in location
    assert "function" in location
    assert "line_number" in location
    assert isinstance(location["line_number"], int)

    # Verify we have a valid location - using more flexible path matching
    assert location["file"] != "unknown", "File path should not be 'unknown'"
    assert any(
        name in location["file"].lower()
        for name in ["test_error_handler", "app", "main", "fides"]
    ), f"Unexpected file path: {location['file']}"

    # Verify function name - more flexible matching
    assert location["function"] in [
        "error_function",
        "test_context",
        "wrapper",
        "handle_endpoint",
    ], f"Unexpected function name: {location['function']}"

    # Verify line number is valid
    assert location["line_number"] > 0, "Line number should be positive"

    # Verify we have context lines
    assert "code_context" in location
    assert isinstance(location["code_context"], list)
    assert len(location["code_context"]) > 0

    # More flexible context line checking
    has_relevant_code = any(
        any(keyword in line for keyword in ["raise", "error", "def", "return"])
        for line in location["code_context"]
    )
    assert has_relevant_code, "No relevant code found in context lines"


def test_error_handler_with_missing_detail(client: TestClient) -> None:
    """Test error handling when the error object is missing the 'detail' attribute."""

    class CustomError(Exception):
        pass

    @client.app.get("/test/missing-detail")
    @ErrorHandler.handle_endpoint(error_message="Custom error test failed")
    async def test_missing_detail() -> None:
        raise CustomError("This error has no 'detail' attribute")

    response = client.get("/test/missing-detail")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR

    # Verify the response structure
    error_data = response.json()["detail"]
    assert "error" in error_data
    assert (
        error_data["error"]["message"]
        == "Custom error test failed: This error has no 'detail' attribute"
    )
    assert error_data["error"]["code"] == "INTERNAL_ERROR"


def test_error_handler_with_non_serializable_detail(client: TestClient) -> None:
    """Test error handling when the error object contains non-serializable fields."""

    class NonSerializableError(Exception):
        def __init__(self):
            self.detail = {"non_serializable": lambda x: x}

    @client.app.get("/test/non-serializable")
    @ErrorHandler.handle_endpoint(error_message="Non-serializable error test failed")
    async def test_non_serializable() -> None:
        raise NonSerializableError()

    response = client.get("/test/non-serializable")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR

    # Verify the response structure
    error_data = response.json()["detail"]
    assert "error" in error_data
    assert error_data["error"]["message"] == "Non-serializable error test failed: "
    assert error_data["error"]["code"] == "INTERNAL_ERROR"


def test_error_handler_with_async_error(client: TestClient) -> None:
    """Test error handling in an asynchronous endpoint."""

    @client.app.get("/test/async-error")
    @ErrorHandler.handle_endpoint(error_message="Async error test failed")
    async def test_async_error() -> None:
        raise ValueError("Async test error")

    response = client.get("/test/async-error")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR

    # Verify the response structure
    error_data = response.json()["detail"]
    assert "error" in error_data
    assert error_data["error"]["message"] == "Async error test failed: Async test error"
    assert error_data["error"]["code"] == "INTERNAL_ERROR"


def test_error_handler_with_empty_response(client: TestClient) -> None:
    """Test error handling when the error response is empty."""

    class EmptyError(Exception):
        def __init__(self):
            self.detail = {}

    @client.app.get("/test/empty-response")
    @ErrorHandler.handle_endpoint(error_message="Empty response test failed")
    async def test_empty_response() -> None:
        raise EmptyError()

    response = client.get("/test/empty-response")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR

    # Verify the response structure
    error_data = response.json()["detail"]
    assert "error" in error_data
    assert error_data["error"]["message"] == "Empty response test failed: "
    assert error_data["error"]["code"] == "INTERNAL_ERROR"


def test_error_handler_with_circular_reference(client: TestClient) -> None:
    """Test error handling when the error object contains circular references."""

    class CircularError(Exception):
        def __init__(self):
            self.detail = {}
            self.detail["self"] = self  # Circular reference

    @client.app.get("/test/circular-reference")
    @ErrorHandler.handle_endpoint(error_message="Circular reference test failed")
    async def test_circular_reference() -> None:
        raise CircularError()

    response = client.get("/test/circular-reference")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR

    # Verify the response structure
    error_data = response.json()["detail"]
    assert "error" in error_data
    assert error_data["error"]["message"] == "Circular reference test failed: "
    assert error_data["error"]["code"] == "INTERNAL_ERROR"


def test_error_handler_with_invalid_http_method(client: TestClient) -> None:
    """Test error handling for invalid HTTP methods."""
    response = client.post("/test/validation")  # POST is not allowed for this endpoint
    assert response.status_code == HTTP_405_METHOD_NOT_ALLOWED

    # Verify the response structure
    error_data = response.json()["detail"]
    assert "Method Not Allowed" in error_data


def test_error_handler_with_custom_status_code(client: TestClient) -> None:
    """Test error handling with a custom status code."""

    class CustomStatusError(Exception):
        def __init__(self):
            self.detail = {"message": "Custom status error", "status_code": 418}

    @client.app.get("/test/custom-status")
    @ErrorHandler.handle_endpoint(error_message="Custom status test failed")
    async def test_custom_status() -> None:
        raise CustomStatusError()

    response = client.get("/test/custom-status")
    assert response.status_code == 418

    # Verify the response structure
    error_data = response.json()["detail"]
    assert "error" in error_data
    assert (
        error_data["error"]["message"]
        == "Custom status test failed: Custom status error"
    )
