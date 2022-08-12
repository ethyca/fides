import json
from typing import Optional

import pytest
from requests import Response

from fidesops.ops.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fidesops.ops.schemas.saas.strategy_configuration import LinkPaginationConfiguration
from fidesops.ops.service.pagination.pagination_strategy_link import (
    LinkPaginationStrategy,
)


@pytest.fixture(scope="function")
def response_with_header_link():
    response = Response()
    response.headers = {"link": "<https://domain.com/customers?page=def>; rel=next"}
    response._content = bytes(
        json.dumps({"customers": [{"id": 1}, {"id": 2}, {"id": 3}]}), "utf-8"
    )
    return response


@pytest.fixture(scope="function")
def response_with_body_link():
    response = Response()
    response._content = bytes(
        json.dumps(
            {
                "customers": [{"id": 1}, {"id": 2}, {"id": 3}],
                "links": {"next": "https://domain.com/customers?page=def"},
            }
        ),
        "utf-8",
    )
    return response


@pytest.fixture(scope="function")
def response_with_empty_string_link():
    response = Response()
    response._content = bytes(
        json.dumps(
            {
                "customers": [{"id": 1}, {"id": 2}, {"id": 3}],
                "links": {"next": ""},
            }
        ),
        "utf-8",
    )
    return response


def test_link_in_headers(response_with_header_link):
    config = LinkPaginationConfiguration(source="headers", rel="next")
    request_params: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/customers",
        query_params={"page": "abc"},
    )

    paginator = LinkPaginationStrategy(config)
    next_request: Optional[SaaSRequestParams] = paginator.get_next_request(
        request_params, {}, response_with_header_link, "customers"
    )
    assert next_request == SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/customers",
        query_params={"page": "def"},
    )


def test_link_in_headers_missing(response_with_body_link):
    config = LinkPaginationConfiguration(source="headers", rel="next")
    request_params: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/customers",
        query_params={"page": "abc"},
    )

    paginator = LinkPaginationStrategy(config)
    next_request: Optional[SaaSRequestParams] = paginator.get_next_request(
        request_params, {}, response_with_body_link, "customers"
    )
    assert next_request is None


def test_link_in_body(response_with_body_link):
    config = LinkPaginationConfiguration(source="body", path="links.next")
    request_params: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/customers",
        query_params={"page": "abc"},
    )

    paginator = LinkPaginationStrategy(config)
    next_request: Optional[SaaSRequestParams] = paginator.get_next_request(
        request_params, {}, response_with_body_link, "customers"
    )
    assert next_request == SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/customers",
        query_params={"page": "def"},
    )


def test_link_in_body_missing(response_with_header_link):
    config = LinkPaginationConfiguration(source="body", path="links.next")
    request_params: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/customers",
        query_params={"page": "abc"},
    )

    paginator = LinkPaginationStrategy(config)
    next_request: Optional[SaaSRequestParams] = paginator.get_next_request(
        request_params, {}, response_with_header_link, "customers"
    )
    assert next_request is None


def test_link_in_body_empty_string(response_with_empty_string_link):
    config = LinkPaginationConfiguration(source="body", path="links.next")
    request_params: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/customers",
        query_params={"page": "abc"},
    )

    paginator = LinkPaginationStrategy(config)
    next_request: Optional[SaaSRequestParams] = paginator.get_next_request(
        request_params, {}, response_with_empty_string_link, "customers"
    )
    assert next_request is None


def test_wrong_source():
    with pytest.raises(ValueError) as exc:
        LinkPaginationConfiguration(source="somewhere", path="links.next")
    assert "value is not a valid enumeration member" in str(exc.value)


def test_config_mismatch():
    with pytest.raises(ValueError) as exc:
        LinkPaginationConfiguration(source="headers", path="links.next")
    assert (
        "The 'rel' value must be specified when accessing the link from the headers"
        in str(exc.value)
    )

    with pytest.raises(ValueError) as exc:
        LinkPaginationConfiguration(source="body", rel="next")
    assert (
        "The 'path' value must be specified when accessing the link from the body"
        in str(exc.value)
    )


def test_headers_present_in_paginated_request(response_with_body_link):
    config = LinkPaginationConfiguration(source="body", path="links.next")
    request_params: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        headers={"x-custom-header": "abc"},
        path="/customers",
        query_params={"page": "abc"},
    )

    paginator = LinkPaginationStrategy(config)
    next_request: Optional[SaaSRequestParams] = paginator.get_next_request(
        request_params, {}, response_with_body_link, "customers"
    )
    assert next_request.headers == request_params.headers
