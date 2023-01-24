# pylint: disable=missing-docstring, redefined-outer-name
"""Integration tests for the API module."""
from json import loads
from typing import Dict

import pytest
import requests
from fideslang import DEFAULT_TAXONOMY, model_list, parse
from pytest import MonkeyPatch
from starlette.testclient import TestClient

from fides.api.ctl.database.crud import get_resource
from fides.api.ctl.routes import health
from fides.api.ctl.routes.util import API_PREFIX
from fides.api.ctl.sql_models import Dataset
from fides.core import api as _api
from fides.core.config import FidesConfig

TAXONOMY_ENDPOINTS = ["data_category", "data_subject", "data_use", "data_qualifier"]


# Helper Functions
def get_existing_key(test_config: FidesConfig, resource_type: str) -> int:
    """Get an ID that is known to exist."""
    return _api.ls(
        test_config.cli.server_url, resource_type, test_config.user.request_headers
    ).json()[-1]["fides_key"]


# Unit Tests
@pytest.mark.unit
def test_generate_resource_urls_no_id(test_config: FidesConfig) -> None:
    """
    Test that the URL generator works as intended.
    """
    server_url = test_config.cli.server_url
    expected_url = f"{server_url}{API_PREFIX}/test/"
    result_url = _api.generate_resource_url(url=server_url, resource_type="test")
    assert expected_url == result_url


@pytest.mark.unit
def test_generate_resource_urls_with_id(test_config: FidesConfig) -> None:
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
        self, test_config: FidesConfig, resources_dict: Dict, endpoint: str
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

    async def test_create_dataset_data_categories_validated(
        self, test_config: FidesConfig, resources_dict: Dict
    ):
        endpoint = "dataset"
        manifest: Dataset = resources_dict[endpoint]
        manifest.collections[0].data_categories = ["bad_category"]

        result = _api.create(
            url=test_config.cli.server_url,
            headers=test_config.user.request_headers,
            json_resource=manifest.json(exclude_none=True),
            resource_type=endpoint,
        )
        assert result.status_code == 422
        assert (
            result.json()["detail"][0]["msg"]
            == "The data category bad_category is not supported."
        )

    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_ls(self, test_config: FidesConfig, endpoint: str) -> None:
        result = _api.ls(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            headers=test_config.user.request_headers,
        )
        print(result.text)
        assert result.status_code == 200

    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_get(self, test_config: FidesConfig, endpoint: str) -> None:
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
        self, test_config: FidesConfig, resources_dict: Dict, endpoint: str
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
        self, test_config: FidesConfig, resources_dict: Dict, endpoint: str
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

    async def test_update_dataset_data_categories_validated(
        self, test_config: FidesConfig, resources_dict: Dict
    ):
        endpoint = "dataset"
        manifest: Dataset = resources_dict[endpoint]
        manifest.collections[0].data_categories = ["bad_category"]

        result = _api.update(
            url=test_config.cli.server_url,
            headers=test_config.user.request_headers,
            resource_type=endpoint,
            json_resource=manifest.json(exclude_none=True),
        )
        assert result.status_code == 422
        assert (
            result.json()["detail"][0]["msg"]
            == "The data category bad_category is not supported."
        )

    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_upsert(
        self, test_config: FidesConfig, resources_dict: Dict, endpoint: str
    ) -> None:
        manifest = resources_dict[endpoint]
        result = _api.upsert(
            url=test_config.cli.server_url,
            headers=test_config.user.request_headers,
            resource_type=endpoint,
            resources=[loads(manifest.json())],
        )
        assert result.status_code == 200

    async def test_upsert_validates_resources_against_pydantic_model(
        self, test_config: FidesConfig, resources_dict: Dict, async_session
    ):
        endpoint = "dataset"
        manifest: Dataset = resources_dict[endpoint]
        dict_manifest = manifest.dict()
        del dict_manifest["organization_fides_key"]

        result = _api.upsert(
            url=test_config.cli.server_url,
            headers=test_config.user.request_headers,
            resource_type=endpoint,
            resources=[dict_manifest],
        )
        assert result.status_code == 200

        resource = await get_resource(Dataset, manifest.fides_key, async_session)
        assert resource.organization_fides_key == "default_organization"

    async def test_upsert_dataset_data_categories_validated(
        self, test_config: FidesConfig, resources_dict: Dict
    ):
        endpoint = "dataset"
        manifest: Dataset = resources_dict[endpoint]
        dict_manifest = manifest.dict()
        dict_manifest["collections"][0]["data_categories"] = ["bad_category"]

        result = _api.upsert(
            url=test_config.cli.server_url,
            headers=test_config.user.request_headers,
            resource_type=endpoint,
            resources=[dict_manifest],
        )
        assert result.status_code == 422
        assert (
            result.json()["detail"][0]["msg"]
            == "The data category bad_category is not supported."
        )

    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_delete(
        self, test_config: FidesConfig, resources_dict: Dict, endpoint: str
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


@pytest.mark.integration
class TestDefaultTaxonomyCrud:
    @pytest.mark.parametrize("endpoint", TAXONOMY_ENDPOINTS)
    def test_api_cannot_delete_default(
        self, test_config: FidesConfig, endpoint: str
    ) -> None:
        resource = getattr(DEFAULT_TAXONOMY, endpoint)[0]

        result = _api.delete(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            resource_id=resource.fides_key,
            headers=test_config.user.request_headers,
        )
        assert result.status_code == 403

    @pytest.mark.parametrize("endpoint", TAXONOMY_ENDPOINTS)
    def test_api_can_update_default(
        self, test_config: FidesConfig, endpoint: str
    ) -> None:
        """Should be able to update as long as `is_default` is not changing"""
        resource = getattr(DEFAULT_TAXONOMY, endpoint)[0]
        json_resource = resource.json(exclude_none=True)

        result = _api.update(
            url=test_config.cli.server_url,
            headers=test_config.user.request_headers,
            resource_type=endpoint,
            json_resource=json_resource,
        )
        assert result.status_code == 200

    @pytest.mark.parametrize("endpoint", TAXONOMY_ENDPOINTS)
    def test_api_can_upsert_default(
        self, test_config: FidesConfig, endpoint: str
    ) -> None:
        """Should be able to upsert as long as `is_default` is not changing"""
        resources = [r.dict() for r in getattr(DEFAULT_TAXONOMY, endpoint)[0:2]]
        result = _api.upsert(
            url=test_config.cli.server_url,
            headers=test_config.user.request_headers,
            resource_type=endpoint,
            resources=resources,
        )
        assert result.status_code == 200

    @pytest.mark.parametrize("endpoint", TAXONOMY_ENDPOINTS)
    def test_api_cannot_create_default_taxonomy(
        self, test_config: FidesConfig, resources_dict: Dict, endpoint: str
    ) -> None:
        manifest = resources_dict[endpoint]
        manifest.is_default = True
        result = _api.create(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            json_resource=manifest.json(exclude_none=True),
            headers=test_config.user.request_headers,
        )
        assert result.status_code == 403

        _api.delete(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            resource_id=manifest.fides_key,
            headers=test_config.user.request_headers,
        )

    @pytest.mark.parametrize("endpoint", TAXONOMY_ENDPOINTS)
    def test_api_cannot_upsert_default_taxonomy(
        self, test_config: FidesConfig, resources_dict: Dict, endpoint: str
    ) -> None:
        manifest = resources_dict[endpoint]
        manifest.is_default = True
        result = _api.upsert(
            url=test_config.cli.server_url,
            headers=test_config.user.request_headers,
            resource_type=endpoint,
            resources=[manifest.dict()],
        )
        assert result.status_code == 403

        _api.delete(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            resource_id=manifest.fides_key,
            headers=test_config.user.request_headers,
        )

    @pytest.mark.parametrize("endpoint", TAXONOMY_ENDPOINTS)
    def test_api_cannot_update_is_default(
        self, test_config: FidesConfig, resources_dict: Dict, endpoint: str
    ) -> None:
        manifest = resources_dict[endpoint]
        _api.create(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            json_resource=manifest.json(exclude_none=True),
            headers=test_config.user.request_headers,
        )

        manifest.is_default = True
        result = _api.update(
            url=test_config.cli.server_url,
            headers=test_config.user.request_headers,
            resource_type=endpoint,
            json_resource=manifest.json(exclude_none=True),
        )
        assert result.status_code == 403

    @pytest.mark.parametrize("endpoint", TAXONOMY_ENDPOINTS)
    def test_api_cannot_upsert_is_default(
        self, test_config: FidesConfig, resources_dict: Dict, endpoint: str
    ) -> None:
        manifest = resources_dict[endpoint]
        manifest.is_default = True
        second_item = manifest.copy()
        second_item.is_default = False

        _api.create(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            json_resource=second_item.json(exclude_none=True),
            headers=test_config.user.request_headers,
        )

        result = _api.upsert(
            url=test_config.cli.server_url,
            headers=test_config.user.request_headers,
            resource_type=endpoint,
            resources=[manifest.dict(), second_item.dict()],
        )
        assert result.status_code == 403

        _api.delete(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            resource_id=manifest.fides_key,
            headers=test_config.user.request_headers,
        )
        _api.delete(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            resource_id=second_item.fides_key,
            headers=test_config.user.request_headers,
        )


@pytest.mark.integration
def test_static_sink(test_config: FidesConfig) -> None:
    """Make sure we are hosting something at / and not getting a 404"""
    response = requests.get(f"{test_config.cli.server_url}")
    assert response.status_code == 200


@pytest.mark.integration
def test_404_on_api_routes(test_config: FidesConfig) -> None:
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
    test_config: FidesConfig,
    database_health: str,
    expected_status_code: int,
    monkeypatch: MonkeyPatch,
    test_client: TestClient,
) -> None:
    def mock_get_db_health(url: str, db) -> str:
        return database_health

    monkeypatch.setattr(health, "get_db_health", mock_get_db_health)
    response = test_client.get(test_config.cli.server_url + "/health")
    assert response.status_code == expected_status_code


@pytest.mark.integration
@pytest.mark.parametrize("endpoint_name", [f"{API_PREFIX}/organization", "/health"])
def test_trailing_slash(test_config: FidesConfig, endpoint_name: str) -> None:
    """URLs both with and without a trailing slash should resolve and not 404"""
    url = f"{test_config.cli.server_url}{endpoint_name}"
    response = requests.get(url)
    assert response.status_code == 200
    response = requests.get(f"{url}/")
    assert response.status_code == 200
