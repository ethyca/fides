"""Tests for the request logging middleware."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Request, Response
from starlette.datastructures import Headers

from fides.api.main import log_request


class TestLogRequest:
    """Tests for the request logging middleware timing functionality."""

    @patch("fides.api.main.logger")
    @pytest.mark.asyncio
    async def test_log_request_timing(self, mock_logger):
        """Test that the log_request middleware correctly calculates request handling time."""
        # Create a mock request
        mock_request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/test",
                "headers": Headers({}),
            },
            receive=None,
        )

        # Create a mock response with artificial delay
        async def mock_call_next(_):
            await asyncio.sleep(0.1)  # 100ms delay
            return Response(status_code=200)

        # Setup mock for chained calls
        bound_logger = MagicMock()
        mock_logger.bind.return_value = bound_logger

        response = await log_request(mock_request, mock_call_next)

        # Verify the response
        assert response.status_code == 200

        # Verify the bind parameters
        mock_logger.bind.assert_called_once()
        bind_args = mock_logger.bind.call_args[1]

        assert bind_args["method"] == "GET"
        assert bind_args["status_code"] == 200
        assert bind_args["path"] == "/test"
        assert "handler_time" in bind_args
        assert bind_args["handler_time"].endswith("ms")

        # Extract the handler_time value and convert it to float for comparison
        handler_time_str = bind_args["handler_time"]
        actual_ms = float(handler_time_str[:-2])  # Remove "ms" and convert to float

        # Timing should be at least 100ms since we added an artificial delay
        assert actual_ms >= 100

        # Verify the info call on the bound logger
        bound_logger.info.assert_called_once_with("Request received")

    @patch("fides.api.main.logger")
    @pytest.mark.asyncio
    async def test_log_request_timing_slow_request(self, mock_logger):
        """
        Test that the log_request middleware correctly calculates request handling time
        for "slow" requests, i.e requests that take longer than 1 second to process.
        """
        # Create a mock request
        mock_request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/test",
                "headers": Headers({}),
            },
            receive=None,
        )

        # Create a mock response with artificial delay
        async def mock_call_next(_):
            await asyncio.sleep(1.5)  # 1500ms delay
            return Response(status_code=200)

        # Setup mock for chained calls
        bound_logger = MagicMock()
        mock_logger.bind.return_value = bound_logger

        response = await log_request(mock_request, mock_call_next)

        # Verify the response
        assert response.status_code == 200

        # Verify the bind parameters
        mock_logger.bind.assert_called_once()
        bind_args = mock_logger.bind.call_args[1]

        assert bind_args["method"] == "GET"
        assert bind_args["status_code"] == 200
        assert bind_args["path"] == "/test"
        assert "handler_time" in bind_args
        assert bind_args["handler_time"].endswith("ms")

        # Extract the handler_time value and convert it to float for comparison
        handler_time_str = bind_args["handler_time"]
        actual_ms = float(handler_time_str[:-2])  # Remove "ms" and convert to float

        # Timing should be at least 1000ms since we added an artificial delay
        assert actual_ms >= 1000

        # Verify the info call on the bound logger
        bound_logger.info.assert_called_once_with("Request received")

    @patch("fides.api.main.logger")
    @pytest.mark.asyncio
    async def test_log_request_error(self, mock_logger):
        """Test that the log_request middleware correctly handles errors."""
        # Create a mock request
        mock_request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/test",
                "headers": Headers({}),
            },
            receive=None,
        )

        # Create a mock response that raises an exception
        async def mock_call_next(_):
            raise ValueError("Test error")

        # Setup mock for chained calls
        bound_logger = MagicMock()
        mock_logger.bind.return_value = bound_logger

        response = await log_request(mock_request, mock_call_next)

        # Verify we get a 500 response for the error
        assert response.status_code == 500

        # Verify the bind parameters
        mock_logger.bind.assert_called_once()
        bind_args = mock_logger.bind.call_args[1]

        assert bind_args["method"] == "GET"
        assert bind_args["status_code"] == 500
        assert bind_args["path"] == "/test"
        assert "handler_time" in bind_args
        assert bind_args["handler_time"].endswith("ms")

        # Verify the info call on the bound logger
        bound_logger.info.assert_called_once_with("Request received")
