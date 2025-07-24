import json
from typing import Optional

import pytest
from requests import Response

from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.schemas.saas.strategy_configuration import CursorPaginationConfiguration
from fides.api.service.pagination.pagination_strategy_cursor import (
    CursorPaginationStrategy,
)


@pytest.fixture(scope="function")
def response_with_body():
    response = Response()
    response._content = bytes(
        json.dumps(
            {
                "conversations": [{"id": 1}, {"id": 2}, {"id": 3}],
                "meta": {"next_cursor": 123},
            }
        ),
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


@pytest.fixture(scope="function")
def response_with_has_next_true():
    response = Response()
    response._content = bytes(
        json.dumps(
            {
                "conversations": [{"id": 1}, {"id": 2}, {"id": 3}],
                "meta": {"next_cursor": 123, "has_next": "true"},
            }
        ),
        "utf-8",
    )
    return response


@pytest.fixture(scope="function")
def response_with_has_next_false():
    response = Response()
    response._content = bytes(
        json.dumps(
            {
                "conversations": [{"id": 1}, {"id": 2}, {"id": 3}],
                "meta": {"next_cursor": 123, "has_next": "false"},
            }
        ),
        "utf-8",
    )
    return response


@pytest.fixture(scope="function")
def response_with_object_has_next_false():
    response = Response()
    response._content = bytes(
        json.dumps(
            {
                "data": [
                    {"id": 1, "has_more": True},
                    {"id": 2, "has_more": True},
                    {"id": 3, "has_more": False},
                ]
            }
        ),
        "utf-8",
    )
    return response


@pytest.fixture(scope="function")
def response_with_object_has_next_true():
    response = Response()
    response._content = bytes(
        json.dumps(
            {
                "data": [
                    {"id": 1, "has_more": True},
                    {"id": 2, "has_more": True},
                ]
            }
        ),
        "utf-8",
    )
    return response


@pytest.fixture(scope="function")
def test_response_with_cursor_object_and_has_next_in_metadata():
    response = Response()
    response._content = bytes(
        json.dumps(
            {
                "data": [
                    {"id": 1, "name": "first"},
                    {"id": 2, "name": "second"},
                ],
                "meta": {"has_more": True},
            }
        ),
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


def test_cursor_has_next_true(response_with_has_next_true):
    config = CursorPaginationConfiguration(
        cursor_param="cursor", field="meta.next_cursor", has_next="meta.has_next"
    )
    request_params: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET, path="/conversations"
    )
    paginator = CursorPaginationStrategy(config)
    next_request: Optional[SaaSRequestParams] = paginator.get_next_request(
        request_params, {}, response_with_has_next_true, "conversations"
    )
    assert next_request == SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/conversations",
        query_params={"cursor": 123},
    )


def test_cursor_has_next_false(response_with_has_next_false):
    config = CursorPaginationConfiguration(
        cursor_param="cursor", field="meta.next_cursor", has_next="meta.has_next"
    )
    request_params: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET, path="/conversations"
    )
    paginator = CursorPaginationStrategy(config)
    next_request: Optional[SaaSRequestParams] = paginator.get_next_request(
        request_params, {}, response_with_has_next_false, "conversations"
    )
    assert next_request is None


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


def test_headers_present_in_paginated_request(response_with_body):
    config = CursorPaginationConfiguration(cursor_param="after", field="id")
    request_params: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        headers={"X-Fides-Token": "token"},
        path="/conversations",
    )
    paginator = CursorPaginationStrategy(config)
    next_request: SaaSRequestParams = paginator.get_next_request(
        request_params, {}, response_with_body, "conversations"
    )
    assert next_request.headers == request_params.headers


def test_cursor_outside_of_data_path(response_with_body):
    config = CursorPaginationConfiguration(
        cursor_param="after", field="meta.next_cursor"
    )
    request_params: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/conversations",
    )
    paginator = CursorPaginationStrategy(config)
    next_request: SaaSRequestParams = paginator.get_next_request(
        request_params, {}, response_with_body, "conversations"
    )
    assert next_request == SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/conversations",
        query_params={"after": 123},
    )


def test_cursor_outside_of_data_path_not_found(response_with_body):
    config = CursorPaginationConfiguration(cursor_param="after", field="meta.next")
    request_params: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/conversations",
    )
    paginator = CursorPaginationStrategy(config)
    next_request: SaaSRequestParams = paginator.get_next_request(
        request_params, {}, response_with_body, "conversations"
    )
    assert next_request is None


def test_cursor_object_has_next_false(response_with_object_has_next_false):
    """Test that pagination stops when the last object has has_more=False"""
    config = CursorPaginationConfiguration(
        cursor_param="after", field="id", has_next="has_more"
    )
    request_params = SaaSRequestParams(method=HTTPMethod.GET, path="/items")
    paginator = CursorPaginationStrategy(config)
    next_request = paginator.get_next_request(
        request_params, {}, response_with_object_has_next_false, "data"
    )
    # Since the last object has has_more=False, we should get None
    assert next_request is None


def test_cursor_object_has_next_true(response_with_object_has_next_true):
    """Test that pagination continues when the last object has has_more=True"""
    config = CursorPaginationConfiguration(
        cursor_param="after", field="id", has_next="has_more"
    )
    request_params = SaaSRequestParams(method=HTTPMethod.GET, path="/items")
    paginator = CursorPaginationStrategy(config)
    next_request = paginator.get_next_request(
        request_params, {}, response_with_object_has_next_true, "data"
    )
    # Since the last object has has_more=True, we should get a request with the cursor
    assert next_request == SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/items",
        query_params={"after": 2},
    )


def test_cursor_object_and_has_next_in_metadata(
    test_response_with_cursor_object_and_has_next_in_metadata,
):
    """Test that pagination works when cursor is in the last object but has_next is in metadata"""
    config = CursorPaginationConfiguration(
        cursor_param="after", field="id", has_next="meta.has_more"
    )
    request_params = SaaSRequestParams(method=HTTPMethod.GET, path="/items")
    paginator = CursorPaginationStrategy(config)
    next_request = paginator.get_next_request(
        request_params,
        {},
        test_response_with_cursor_object_and_has_next_in_metadata,
        "data",
    )
    # Should get next request since meta.has_more is True and cursor (id) is found in last object
    assert next_request == SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/items",
        query_params={"after": 2},
    )
