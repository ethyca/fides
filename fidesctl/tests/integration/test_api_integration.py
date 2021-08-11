"""Integration tests for the API module."""
from typing import Dict

import pytest

from fidesctl.core.config import generate_request_headers
from fidesctl.core import api as _api, parse
from fidesctl.core.models import MODEL_LIST

# Helper Functions
def get_existing_id(test_config: str, object_type: str) -> int:
    """Get an ID that is known to exist."""
    return _api.show(
        test_config.cli.server_url, object_type, test_config.user.request_headers
    ).json()["data"][-1]["id"]


def get_id_from_key(test_config: str, object_type: str, object_key: str) -> int:
    return _api.find(
        test_config.cli.server_url,
        object_type,
        object_key,
        test_config.user.request_headers,
    ).json()["data"]["id"]


# Tests
def test_api_ping(test_config):
    assert _api.ping(test_config.cli.server_url).status_code == 200


@pytest.mark.parametrize("endpoint", MODEL_LIST)
def test_api_show(test_config, endpoint):
    result = _api.show(
        url=test_config.cli.server_url,
        object_type=endpoint,
        headers=test_config.user.request_headers,
    )
    print(result.text)
    assert result.status_code == 200


@pytest.mark.parametrize("endpoint", MODEL_LIST)
def test_api_create(test_config, objects_dict, endpoint):
    manifest = objects_dict[endpoint]
    print(manifest.json(exclude_none=True))
    result = _api.create(
        url=test_config.cli.server_url,
        object_type=endpoint,
        json_object=manifest.json(exclude_none=True),
        headers=test_config.user.request_headers,
    )
    print(result.text)
    assert result.status_code == 200


@pytest.mark.parametrize("endpoint", MODEL_LIST)
def test_api_get(test_config, endpoint):
    existing_id = get_existing_id(test_config, endpoint)
    result = _api.get(
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
        object_type=endpoint,
        object_id=existing_id,
    )
    print(result.text)
    assert result.status_code == 200


@pytest.mark.parametrize("endpoint", MODEL_LIST)
def test_api_find(test_config, objects_dict, endpoint):
    manifest = objects_dict[endpoint]
    object_key = manifest.fidesKey if endpoint != "user" else manifest.userName
    result = _api.find(
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
        object_type=endpoint,
        object_key=object_key,
    )
    print(result.text)
    assert result.status_code == 200


@pytest.mark.parametrize("endpoint", MODEL_LIST)
def test_sent_is_received(test_config, objects_dict, endpoint):
    """
    Confirm that the object and values that we send are the
    same as the object that the server returns.
    """
    manifest = objects_dict[endpoint]
    object_key = manifest.fidesKey if endpoint != "user" else manifest.userName

    print(manifest.json(exclude_none=True))
    result = _api.find(
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
        object_type=endpoint,
        object_key=object_key,
    )
    print(result.text)
    assert result.status_code == 200
    parsed_result = parse.parse_manifest(endpoint, result.json()["data"])

    # This is a hack because the system returns objects with IDs
    manifest.id = parsed_result.id
    if endpoint == "user":
        manifest.apiKey = parsed_result.apiKey

    assert parsed_result == manifest


@pytest.mark.parametrize("endpoint", MODEL_LIST)
def test_api_update(test_config, objects_dict, endpoint):

    manifest = objects_dict[endpoint]

    update_id = get_existing_id(test_config, endpoint)
    result = _api.update(
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
        object_type=endpoint,
        object_id=update_id,
        json_object=manifest.json(exclude_none=True),
    )
    print(result.text)
    assert result.status_code == 200


@pytest.mark.parametrize("endpoint", MODEL_LIST)
def test_api_delete(test_config, objects_dict, endpoint):
    manifest = objects_dict[endpoint]
    object_key = manifest.fidesKey if endpoint != "user" else manifest.userName
    delete_id = get_id_from_key(test_config, endpoint, object_key)

    assert delete_id != 1
    result = _api.delete(
        url=test_config.cli.server_url,
        object_type=endpoint,
        object_id=delete_id,
        headers=test_config.user.request_headers,
    )
    print(result.text)
    assert result.status_code == 200
