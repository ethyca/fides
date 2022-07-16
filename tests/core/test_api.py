# pylint: disable=missing-docstring, redefined-outer-name
"""Integration tests for the API module."""
from json import loads
from typing import Dict

import pytest
import requests
from pytest import MonkeyPatch
from starlette.testclient import TestClient

from fidesapi import main
from fidesctl.core import api as _api
from fidesctl.core.config import FidesctlConfig
from fidesctl.core.utils import API_PREFIX
from fideslang import model_list, parse


# Helper Functions
def get_existing_key(test_config: FidesctlConfig, resource_type: str) -> int:
    """Get an ID that is known to exist."""
    return _api.ls(
        test_config.cli.server_url, resource_type, test_config.user.request_headers
    ).json()[-1]["fides_key"]


# Unit Tests
@pytest.mark.unit
def test_generate_resource_urls_no_id(test_config: FidesctlConfig) -> None:
    """
    Test that the URL generator works as intended.
    """
    server_url = test_config.cli.server_url
    expected_url = f"{server_url}{API_PREFIX}/test/"
    result_url = _api.generate_resource_url(url=server_url, resource_type="test")
    assert expected_url == result_url


@pytest.mark.unit
def test_generate_resource_urls_with_id(test_config: FidesctlConfig) -> None:
    """
    Test that the URL generator works as intended.
    """
    server_url = test_config.cli.server_url
    expected_url = f"{server_url}{API_PREFIX}/test/1"
    result_url = _api.generate_resource_url(
        url=server_url,
        resource_type="test",
        resource_id="1",
    )
    assert expected_url == result_url


@pytest.mark.integration
class TestCrud:
    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_create(
        self, test_config: FidesctlConfig, resources_dict: Dict, endpoint: str
    ) -> None:
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

    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_ls(self, test_config: FidesctlConfig, endpoint: str) -> None:
        result = _api.ls(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            headers=test_config.user.request_headers,
        )
        print(result.text)
        assert result.status_code == 200

    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_get(self, test_config: FidesctlConfig, endpoint: str) -> None:
        existing_id = get_existing_key(test_config, endpoint)
        result = _api.get(
            url=test_config.cli.server_url,
            headers=test_config.user.request_headers,
            resource_type=endpoint,
            resource_id=existing_id,
        )
        print(result.text)
        assert result.status_code == 200

    @pytest.mark.parametrize("endpoint", model_list)
    def test_sent_is_received(
        self, test_config: FidesctlConfig, resources_dict: Dict, endpoint: str
    ) -> None:
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

    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_update(
        self, test_config: FidesctlConfig, resources_dict: Dict, endpoint: str
    ) -> None:
        manifest = resources_dict[endpoint]
        result = _api.update(
            url=test_config.cli.server_url,
            headers=test_config.user.request_headers,
            resource_type=endpoint,
            json_resource=manifest.json(exclude_none=True),
        )
        print(result.text)
        assert result.status_code == 200

    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_upsert(
        self, test_config: FidesctlConfig, resources_dict: Dict, endpoint: str
    ) -> None:
        manifest = resources_dict[endpoint]
        result = _api.upsert(
            url=test_config.cli.server_url,
            headers=test_config.user.request_headers,
            resource_type=endpoint,
            resources=[loads(manifest.json())],
        )
        assert result.status_code == 200

    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_delete(
        self, test_config: FidesctlConfig, resources_dict: Dict, endpoint: str
    ) -> None:
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


# This test will fail if certain other tests run before it, due to a non-deterministic bug in the code
# Keeping the order as-is is a temporary fix
@pytest.mark.integration
@pytest.mark.parametrize(
    "resource_type", ["data_category", "data_use", "data_qualifier"]
)
def test_visualize(
    setup_db: str, test_config: FidesctlConfig, resource_type: str
) -> None:
    response = requests.get(
        f"{test_config.cli.server_url}{API_PREFIX}/{resource_type}/visualize/graphs"
    )
    assert response.status_code == 200


@pytest.mark.integration
def test_static_sink(test_config: FidesctlConfig) -> None:
    """Make sure we are hosting something at / and not getting a 404"""
    response = requests.get(f"{test_config.cli.server_url}")
    assert response.status_code == 200


@pytest.mark.integration
def test_404_on_api_routes(test_config: FidesctlConfig) -> None:
    """Should get a 404 on routes that start with API_PREFIX but do not exist"""
    response = requests.get(
        f"{test_config.cli.server_url}{API_PREFIX}/path/that/does/not/exist"
    )
    assert response.status_code == 404


# Integration Tests
@pytest.mark.integration
@pytest.mark.parametrize(
    "database_health, expected_status_code",
    [("healthy", 200), ("needs migration", 200), ("unhealthy", 503)],
)
def test_api_ping(
    test_config: FidesctlConfig,
    database_health: str,
    expected_status_code: int,
    monkeypatch: MonkeyPatch,
    test_client: TestClient,
) -> None:
    def mock_get_db_health(url: str) -> str:
        return database_health

    monkeypatch.setattr(main, "get_db_health", mock_get_db_health)
    response = test_client.get(test_config.cli.server_url + API_PREFIX + "/health")
    assert response.status_code == expected_status_code
