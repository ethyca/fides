from typing import Any, Dict

import pytest
from loguru import logger
from requests import PreparedRequest, Request, Response

from fides.api.util.logger_context_utils import (
    Contextualizable,
    ErrorGroup,
    LoggerContextKeys,
    log_context,
    request_details,
)


class TestLogContextDecorator:
    def test_log_context_without_contextualizable_params(self, loguru_caplog):
        @log_context
        def func():
            logger.info("returning")
            return

        func()

        assert loguru_caplog.records[0].extra == {}

    def test_log_context_with_contextualizable_params(self, loguru_caplog):
        class LoggableClass(Contextualizable):
            def get_log_context(self) -> Dict[LoggerContextKeys, Any]:
                return {LoggerContextKeys.privacy_request_id: "123"}

        @log_context
        def func(param: LoggableClass):
            logger.info("returning")
            return param

        func(LoggableClass())

        assert loguru_caplog.records[0].extra == {
            LoggerContextKeys.privacy_request_id.value: "123"
        }

    def test_log_context_with_additional_context(self, loguru_caplog):
        @log_context(one_more_thing="456")
        def func():
            logger.info("returning")
            return

        func()

        assert loguru_caplog.records[0].extra == {
            "one_more_thing": "456",
        }

    def test_log_context_with_contextualizable_params_and_additional_context(
        self, loguru_caplog
    ):
        class LoggableClass(Contextualizable):
            def get_log_context(self) -> Dict[LoggerContextKeys, Any]:
                return {LoggerContextKeys.privacy_request_id: "123"}

        @log_context(one_more_thing="456")
        def func(param: LoggableClass):
            logger.info("returning")
            return param

        func(LoggableClass())

        assert loguru_caplog.records[0].extra == {
            LoggerContextKeys.privacy_request_id.value: "123",
            "one_more_thing": "456",
        }

    def test_log_context_with_captured_args(self, loguru_caplog):
        """Test that arguments are captured and mapped to context keys correctly"""

        @log_context(capture_args={"task_id": LoggerContextKeys.task_id})
        def func(task_id: str):
            logger.info("processing task")
            return task_id

        func(task_id="abc123")

        assert loguru_caplog.records[0].extra == {
            LoggerContextKeys.task_id.value: "abc123"
        }

    def test_log_context_with_captured_args_and_contextualizable(self, loguru_caplog):
        """Test that both captured args and Contextualizable objects work together"""

        class LoggableClass(Contextualizable):
            def get_log_context(self) -> Dict[LoggerContextKeys, Any]:
                return {LoggerContextKeys.privacy_request_id: "123"}

        @log_context(capture_args={"task_id": LoggerContextKeys.task_id})
        def func(param: LoggableClass, task_id: str):
            logger.info("processing")
            return param

        func(LoggableClass(), task_id="abc123")

        assert loguru_caplog.records[0].extra == {
            LoggerContextKeys.privacy_request_id.value: "123",
            LoggerContextKeys.task_id.value: "abc123",
        }

    def test_log_context_with_captured_args_and_additional_context(self, loguru_caplog):
        """Test that captured args work with additional context"""

        @log_context(
            capture_args={"task_id": LoggerContextKeys.task_id}, tenant="example"
        )
        def func(task_id: str):
            logger.info("processing")
            return task_id

        func(task_id="abc123")

        assert loguru_caplog.records[0].extra == {
            LoggerContextKeys.task_id.value: "abc123",
            "tenant": "example",
        }

    def test_log_context_with_missing_captured_arg(self, loguru_caplog):
        """Test that missing captured args don't cause issues"""

        @log_context(capture_args={"task_id": LoggerContextKeys.task_id})
        def func(different_param: str):
            logger.info("processing")
            return different_param

        func(different_param="abc123")

        assert loguru_caplog.records[0].extra == {}

    def test_log_context_with_multiple_captured_args(self, loguru_caplog):
        """Test capturing multiple arguments"""

        @log_context(
            capture_args={
                "task_id": LoggerContextKeys.task_id,
                "request_id": LoggerContextKeys.privacy_request_id,
            }
        )
        def func(task_id: str, request_id: str):
            logger.info("processing")
            return task_id, request_id

        func(task_id="abc123", request_id="req456")

        assert loguru_caplog.records[0].extra == {
            LoggerContextKeys.task_id.value: "abc123",
            LoggerContextKeys.privacy_request_id.value: "req456",
        }

    def test_log_context_with_positional_captured_args(self, loguru_caplog):
        """Test that captured args work with positional arguments"""

        @log_context(capture_args={"task_id": LoggerContextKeys.task_id})
        def func(other_param: str, task_id: str):
            logger.info("processing")
            return other_param, task_id

        func("something", "abc123")

        assert loguru_caplog.records[0].extra == {
            LoggerContextKeys.task_id.value: "abc123"
        }

    def test_log_context_with_multiple_positional_captured_args(self, loguru_caplog):
        """Test that multiple captured args work with positional arguments"""

        @log_context(
            capture_args={
                "task_id": LoggerContextKeys.task_id,
                "request_id": LoggerContextKeys.privacy_request_id,
            }
        )
        def func(other_param: str, task_id: str, request_id: str):
            logger.info("processing")
            return other_param, task_id, request_id

        # Pass all arguments as positional arguments
        func("something", "abc123", "req456")

        assert loguru_caplog.records[0].extra == {
            LoggerContextKeys.task_id.value: "abc123",
            LoggerContextKeys.privacy_request_id.value: "req456",
        }

    def test_log_context_with_mixed_positional_and_keyword_only_args(
        self, loguru_caplog
    ):
        """Test that captured args work with functions that have a mix of positional and keyword-only arguments"""

        @log_context(
            capture_args={
                "task_id": LoggerContextKeys.task_id,
                "request_id": LoggerContextKeys.privacy_request_id,
            }
        )
        def func(task_id: str, *, request_id: str):
            logger.info("processing")
            return task_id, request_id

        # Pass task_id as positional and request_id as keyword (required)
        func("abc123", request_id="req456")

        assert loguru_caplog.records[0].extra == {
            LoggerContextKeys.task_id.value: "abc123",
            LoggerContextKeys.privacy_request_id.value: "req456",
        }

    def test_log_context_with_keyword_only_args(self, loguru_caplog):
        """Test that captured args work with functions that have only keyword-only arguments"""

        @log_context(
            capture_args={
                "task_id": LoggerContextKeys.task_id,
                "request_id": LoggerContextKeys.privacy_request_id,
            }
        )
        def func(*, task_id: str, request_id: str):
            logger.info("processing")
            return task_id, request_id

        # All arguments must be passed as keywords
        func(task_id="abc123", request_id="req456")

        assert loguru_caplog.records[0].extra == {
            LoggerContextKeys.task_id.value: "abc123",
            LoggerContextKeys.privacy_request_id.value: "req456",
        }

    def test_log_context_with_default_parameters(self, loguru_caplog):
        """Test that captured args work with functions that have default parameters"""

        @log_context(
            capture_args={
                "task_id": LoggerContextKeys.task_id,
                "request_id": LoggerContextKeys.privacy_request_id,
            }
        )
        def func(task_id: str = "default_task", request_id: str = "default_request"):
            logger.info("processing")
            return task_id, request_id

        # Call with no arguments - should use defaults
        func()

        assert loguru_caplog.records[0].extra == {
            LoggerContextKeys.task_id.value: "default_task",
            LoggerContextKeys.privacy_request_id.value: "default_request",
        }

    def test_log_context_with_overridden_default_parameters(self, loguru_caplog):
        """Test that captured args work with functions where default parameters are overridden"""

        @log_context(
            capture_args={
                "task_id": LoggerContextKeys.task_id,
                "request_id": LoggerContextKeys.privacy_request_id,
            }
        )
        def func(task_id: str = "default_task", request_id: str = "default_request"):
            logger.info("processing")
            return task_id, request_id

        # Override only one default parameter
        func(task_id="abc123")

        assert loguru_caplog.records[0].extra == {
            LoggerContextKeys.task_id.value: "abc123",
            LoggerContextKeys.privacy_request_id.value: "default_request",
        }


class TestDetailFunctions:
    @pytest.fixture
    def prepared_request(self) -> PreparedRequest:
        return Request(
            method="POST",
            url="https://test/users",
            headers={"Content-type": "application/json"},
            params={"a": "b"},
            data={"name": "test"},
        ).prepare()

    def test_request_details(self, prepared_request):
        response = Response()
        response.status_code = 200
        response._content = "test response".encode()

        assert request_details(prepared_request, response) == {
            "method": "POST",
            "url": "https://test/users?a=b",
            "body": "name=test",
            "response": "test response",
            "status_code": 200,
        }

    @pytest.mark.usefixtures("test_config_dev_mode_disabled")
    def test_request_details_dev_mode_disabled(self, prepared_request):
        response = Response()
        response.status_code = 200
        response._content = "test response".encode()

        assert request_details(prepared_request, response) == {
            "method": "POST",
            "url": "https://test/users?a=b",
            "status_code": 200,
        }

    @pytest.mark.parametrize(
        "ignore_error, status_code, error_group",
        [
            (True, 401, ErrorGroup.authentication_error.value),
            (True, 403, ErrorGroup.authentication_error.value),
            (True, 400, ErrorGroup.client_error.value),
            (True, 500, ErrorGroup.server_error.value),
            (False, 401, ErrorGroup.authentication_error.value),
            (False, 403, ErrorGroup.authentication_error.value),
            (False, 400, ErrorGroup.client_error.value),
            (False, 500, ErrorGroup.server_error.value),
        ],
    )
    def test_request_details_with_errors(
        self, ignore_error, status_code, error_group, prepared_request
    ):
        response = Response()
        response.status_code = status_code
        response._content = "test response".encode()

        expected_detail = {
            "method": "POST",
            "url": "https://test/users?a=b",
            "body": "name=test",
            "response": "test response",
            "status_code": status_code,
        }
        if not ignore_error:
            expected_detail["error_group"] = error_group

        assert (
            request_details(prepared_request, response, ignore_error) == expected_detail
        )

    @pytest.mark.parametrize(
        "ignore_error, status_code, error_group",
        [
            (True, 401, ErrorGroup.authentication_error.value),
            (True, 403, ErrorGroup.authentication_error.value),
            (True, 400, ErrorGroup.client_error.value),
            (True, 500, ErrorGroup.server_error.value),
            (False, 401, ErrorGroup.authentication_error.value),
            (False, 403, ErrorGroup.authentication_error.value),
            (False, 400, ErrorGroup.client_error.value),
            (False, 500, ErrorGroup.server_error.value),
        ],
    )
    @pytest.mark.usefixtures("test_config_dev_mode_disabled")
    def test_request_details_with_errors_dev_mode_disabled(
        self, ignore_error, status_code, error_group, prepared_request
    ):
        response = Response()
        response.status_code = status_code
        response._content = "test response".encode()

        expected_detail = {
            "method": "POST",
            "url": "https://test/users?a=b",
            "status_code": status_code,
        }
        if not ignore_error:
            expected_detail["error_group"] = error_group

        assert (
            request_details(prepared_request, response, ignore_error) == expected_detail
        )
