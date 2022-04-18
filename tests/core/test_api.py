"""Integration tests for the API module."""

import pytest
import requests
from json import loads

from fidesctl.core import api as _api
from fideslang import parse, model_list

# Helper Functions
def get_existing_key(test_config, resource_type: str) -> int:
    """Get an ID that is known to exist."""
    return _api.ls(
        test_config.cli.server_url, resource_type, test_config.user.request_headers
    ).json()[-1]["fides_key"]


# Unit Tests
@pytest.mark.unit
def test_generate_resource_urls_no_id(test_config):
    """
    Test that the URL generator works as intended.
    """
    expected_url = f"{test_config}/test/"
    result_url = _api.generate_resource_url(url=test_config, resource_type="test")
    assert expected_url == result_url


@pytest.mark.unit
def test_generate_resource_urls_with_id(test_config):
    """
    Test that the URL generator works as intended.
    """
    expected_url = f"{test_config}/test/1"
    result_url = _api.generate_resource_url(
        url=test_config,
        resource_type="test",
        resource_id="1",
    )
    assert expected_url == result_url


# Integration Tests
@pytest.mark.integration
def test_api_ping(test_config):
    assert _api.ping(test_config.cli.server_url + "/health").status_code == 200


@pytest.mark.integration
@pytest.mark.parametrize("endpoint", model_list)
def test_api_create(test_config, resources_dict, endpoint):
    manifest = resources_dict[endpoint]
    print(manifest.json(exclude_none=True))
    result = _api.create(
        url=test_config.cli.server_url,
        resource_type=endpoint,
        json_resource=manifest.json(exclude_none=True),
        headers=test_config.user.request_headers,
    )
    print(result.text)
    assert result.status_code == 201


@pytest.mark.integration
@pytest.mark.parametrize("endpoint", model_list)
def test_api_ls(test_config, endpoint):
    result = _api.ls(
        url=test_config.cli.server_url,
        resource_type=endpoint,
        headers=test_config.user.request_headers,
    )
    print(result.text)
    assert result.status_code == 200


@pytest.mark.integration
@pytest.mark.parametrize("endpoint", model_list)
def test_api_get(test_config, endpoint):
    existing_id = get_existing_key(test_config, endpoint)
    result = _api.get(
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
        resource_type=endpoint,
        resource_id=existing_id,
    )
    print(result.text)
    assert result.status_code == 200


@pytest.mark.integration
@pytest.mark.parametrize("endpoint", model_list)
def test_sent_is_received(test_config, resources_dict, endpoint):
    """
    Confirm that the resource and values that we send are the
    same as the resource that the server returns.
    """
    manifest = resources_dict[endpoint]
    resource_key = manifest.fides_key if endpoint != "user" else manifest.userName

    print(manifest.json(exclude_none=True))
    result = _api.get(
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
        resource_type=endpoint,
        resource_id=resource_key,
    )
    print(result.text)
    assert result.status_code == 200
    parsed_result = parse.parse_dict(endpoint, result.json())

    assert parsed_result == manifest


@pytest.mark.integration
@pytest.mark.parametrize("endpoint", model_list)
def test_api_update(test_config, resources_dict, endpoint):

    manifest = resources_dict[endpoint]
    result = _api.update(
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
        resource_type=endpoint,
        json_resource=manifest.json(exclude_none=True),
    )
    print(result.text)
    assert result.status_code == 200


@pytest.mark.integration
@pytest.mark.parametrize("endpoint", model_list)
def test_api_upsert(test_config, resources_dict, endpoint):
    manifest = resources_dict[endpoint]
    result = _api.upsert(
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
        resource_type=endpoint,
        resources=[loads(manifest.json())],
    )

    assert result.status_code == 200


@pytest.mark.integration
@pytest.mark.parametrize("endpoint", model_list)
def test_api_delete(test_config, resources_dict, endpoint):
    manifest = resources_dict[endpoint]
    resource_key = manifest.fides_key if endpoint != "user" else manifest.userName

    result = _api.delete(
        url=test_config.cli.server_url,
        resource_type=endpoint,
        resource_id=resource_key,
        headers=test_config.user.request_headers,
    )
    print(result.text)
    assert result.status_code == 200


@pytest.mark.integration
@pytest.mark.parametrize(
    "resource_type", ["data_category", "data_use", "data_qualifier"]
)
def test_visualize(test_config, resource_type):
    response = requests.get(
        f"{test_config.cli.server_url}/{resource_type}/visualize/graphs"
    )
    assert response.status_code == 200
