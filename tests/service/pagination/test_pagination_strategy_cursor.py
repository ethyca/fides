import json
from typing import Optional

import pytest
from requests import Response
from fidesops.schemas.saas.shared_schemas import SaaSRequestParams, HTTPMethod
from fidesops.schemas.saas.strategy_configuration import CursorPaginationConfiguration
from fidesops.service.pagination.pagination_strategy_cursor import (
    CursorPaginationStrategy,
)


@pytest.fixture(scope="function")
def response_with_body():
    response = Response()
    response._content = bytes(
        json.dumps({"conversations": [{"id": 1}, {"id": 2}, {"id": 3}]}),
        "utf-8",
    )
    return response


@pytest.fixture(scope="function")
def response_with_empty_list():
    response = Response()
    response._content = bytes(
        json.dumps({"conversations": []}),
        "utf-8",
    )
    return response


def test_cursor(response_with_body):
    config = CursorPaginationConfiguration(cursor_param="after", field="id")
    request_params: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET, path="/conversations"
    )
    paginator = CursorPaginationStrategy(config)
    next_request: Optional[SaaSRequestParams] = paginator.get_next_request(
        request_params, {}, response_with_body, "conversations"
    )
    assert next_request == SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/conversations",
        query_params={"after": 3},
    )


def test_missing_cursor_value(response_with_body):
    config = CursorPaginationConfiguration(cursor_param="after", field="hash")
    request_params: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/conversations",
    )

    paginator = CursorPaginationStrategy(config)
    next_request: SaaSRequestParams = paginator.get_next_request(
        request_params, {}, response_with_body, "conversations"
    )
    assert next_request is None


def test_cursor_with_empty_list(response_with_empty_list):
    config = CursorPaginationConfiguration(cursor_param="after", field="id")
    request_params: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/conversations",
    )

    paginator = CursorPaginationStrategy(config)
    next_request: SaaSRequestParams = paginator.get_next_request(
        request_params, {}, response_with_empty_list, "conversations"
    )
    assert next_request is None
