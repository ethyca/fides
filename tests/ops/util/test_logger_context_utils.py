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
