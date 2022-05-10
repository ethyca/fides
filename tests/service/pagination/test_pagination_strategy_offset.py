import json
from typing import Optional

import pytest
from requests import Response
from fidesops.schemas.saas.saas_config import SaaSRequest
from fidesops.schemas.saas.shared_schemas import SaaSRequestParams, HTTPMethod
from fidesops.common_exceptions import FidesopsException
from fidesops.schemas.saas.strategy_configuration import (
    OffsetPaginationConfiguration,
)
from fidesops.service.pagination.pagination_strategy_offset import (
    OffsetPaginationStrategy,
)


@pytest.fixture(scope="function")
def response_with_body():
    response = Response()
    response._content = bytes(
        json.dumps({"conversations": [{"id": 1}, {"id": 2}, {"id": 3}]}),
        "utf-8",
    )
    return response


def test_offset(response_with_body):
    config = OffsetPaginationConfiguration(
        incremental_param="page", increment_by=1, limit=10
    )
    request_params: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/conversations",
        query_params={"page": 1},
    )
    paginator = OffsetPaginationStrategy(config)
    next_request: Optional[SaaSRequestParams] = paginator.get_next_request(
        request_params, {}, response_with_body, "conversations"
    )
    assert next_request == SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/conversations",
        query_params={"page": 2},
    )


def test_offset_with_connector_param_reference(response_with_body):
    config = OffsetPaginationConfiguration(
        incremental_param="page",
        increment_by=1,
        limit={"connector_param": "limit"},
    )
    connector_params = {"limit": 10}
    request_params: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/conversations",
        query_params={"page": 1},
    )

    paginator = OffsetPaginationStrategy(config)
    next_request: Optional[SaaSRequestParams] = paginator.get_next_request(
        request_params, connector_params, response_with_body, "conversations"
    )
    assert next_request == SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/conversations",
        query_params={"page": 2},
    )


def test_offset_with_connector_param_reference_not_found(response_with_body):
    config = OffsetPaginationConfiguration(
        incremental_param="page",
        increment_by=1,
        limit={"connector_param": "limit"},
    )
    request_params: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/conversations",
        query_params={"page": 1},
    )

    paginator = OffsetPaginationStrategy(config)
    with pytest.raises(FidesopsException) as exc:
        paginator.get_next_request(
            request_params, {}, response_with_body, "conversations"
        )
    assert (
        f"Unable to find value for 'limit' with the connector_param reference '{config.limit.connector_param}'"
        == str(exc.value)
    )


def test_offset_limit(response_with_body):
    config = OffsetPaginationConfiguration(
        incremental_param="page", increment_by=1, limit=10
    )
    request_params: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/conversations",
        query_params={"page": 10},
    )

    paginator = OffsetPaginationStrategy(config)
    next_request: SaaSRequestParams = paginator.get_next_request(
        request_params, {}, response_with_body, "conversations"
    )
    assert next_request is None


def test_offset_increment_by_zero():
    with pytest.raises(ValueError) as exc:
        OffsetPaginationConfiguration(
            incremental_param="page", increment_by=0, limit=10
        )
    assert f"'increment_by' cannot be zero" in str(exc.value)


def test_offset_increment_by_negative():
    with pytest.raises(ValueError) as exc:
        OffsetPaginationConfiguration(
            incremental_param="page", increment_by=-1, limit=10
        )
    assert f"'increment_by' cannot be negative" in str(exc.value)


def test_offset_missing_start_value(response_with_body):
    config = OffsetPaginationConfiguration(
        incremental_param="page", increment_by=1, limit=10
    )
    request_params: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/conversations",
        query_params={"row": 1},
    )

    paginator = OffsetPaginationStrategy(config)
    with pytest.raises(FidesopsException) as exc:
        paginator.get_next_request(
            request_params, {}, response_with_body, "conversations"
        )
    assert (
        f"Unable to find query param named '{config.incremental_param}' in request"
        == str(exc.value)
    )


def test_validate_request():
    query_params = [{"name": "page", "value": 1}]
    pagination = {
        "strategy": "offset",
        "configuration": {
            "incremental_param": "page",
            "increment_by": 1,
            "limit": 10,
        },
    }
    SaaSRequest(
        method="GET", path="/test", query_params=query_params, pagination=pagination
    )


def test_validate_request_missing_param():
    query_params = [{"name": "row", "value": 1}]
    pagination = {
        "strategy": "offset",
        "configuration": {
            "incremental_param": "page",
            "increment_by": 1,
            "limit": 10,
        },
    }
    with pytest.raises(ValueError) as exc:
        SaaSRequest(
            method="GET", path="/test", query_params=query_params, pagination=pagination
        )
    assert "Query param 'page' not found." in str(exc.value)
