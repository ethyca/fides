from typing import Dict

import pytest
from starlette.testclient import TestClient

from fides.api.ctl.database.crud import delete_resource
from fides.api.ctl.sql_models import Dataset as CtlDataset  # type: ignore[attr-defined]
from fides.core import api as _api
from fides.core import dataset as _dataset
from fides.lib.oauth.api.urn_registry import V1_URL_PREFIX
from tests.ops.fixtures.application_fixtures import load_dataset_as_string


@pytest.fixture()
def test_dataset() -> Dict:
    test_resource = {"foo": ["1", "2"]}
    test_resource_dataset = _dataset.create_db_dataset("ds", test_resource)
    return test_resource_dataset.dict()


@pytest.fixture
def example_yaml_dataset() -> str:
    example_filename = "data/dataset/postgres_example_test_dataset.yml"
    return load_dataset_as_string(example_filename)


@pytest.fixture
def example_yaml_datasets() -> str:
    example_filename = "data/dataset/example_test_datasets.yml"
    return load_dataset_as_string(example_filename)


@pytest.fixture
def example_invalid_yaml_dataset() -> str:
    example_filename = "data/dataset/example_test_dataset.invalid"
    return load_dataset_as_string(example_filename)


class TestYamlDatasetCreate:
    @pytest.fixture
    def dataset_url(self) -> str:
        return V1_URL_PREFIX + "/yml/dataset"

    def test_post_yaml_dataset_invalid_content_type(
        self,
        dataset_url: str,
        test_dataset,
        test_client: TestClient,
    ) -> None:
        response = test_client.post(dataset_url, json=test_dataset)
        assert response.status_code == 415

    def test_post_yaml_dataset(
        self,
        dataset_url: str,
        example_yaml_dataset,
        test_client: TestClient,
        test_config,
    ) -> None:
        headers = {"Content-type": "application/x-yaml"}
        response = test_client.post(
            dataset_url, headers=headers, data=example_yaml_dataset
        )
        assert response.status_code == 201
        assert response.json()["fides_key"] == "postgres_example_test_dataset"

        _api.delete(
            url=test_config.cli.server_url,
            resource_type="dataset",
            resource_id="postgres_example_test_dataset",
            headers=test_config.user.request_headers,
        )

    def test_post_yaml_dataset_invalid_content(
        self,
        dataset_url: str,
        example_invalid_yaml_dataset,
        test_client: TestClient,
    ) -> None:
        headers = {"Content-type": "application/x-yaml"}
        response = test_client.post(
            dataset_url, headers=headers, data=example_invalid_yaml_dataset
        )
        assert response.status_code == 400

    def test_post_no_datasets(
        self,
        dataset_url: str,
        test_client: TestClient,
    ) -> None:
        headers = {"Content-type": "application/x-yaml"}
        response = test_client.post(dataset_url, headers=headers, data="")
        assert response.status_code == 400
        assert response.json()["detail"] == "No datasets in request body"

    def test_post_multiple_yaml_datasets(
        self,
        dataset_url: str,
        example_yaml_datasets,
        test_client: TestClient,
    ) -> None:
        headers = {"Content-type": "application/x-yaml"}
        response = test_client.post(
            dataset_url, headers=headers, data=example_yaml_datasets
        )
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "Only one dataset can be submitted through this endpoint"
        )


class TestYamlDatasetUpsert:
    @pytest.fixture
    def dataset_url(self) -> str:
        return V1_URL_PREFIX + "/yml/dataset/upsert"

    def test_post_yaml_dataset_invalid_content_type(
        self,
        dataset_url: str,
        test_dataset,
        test_client: TestClient,
    ) -> None:
        response = test_client.post(dataset_url, json=test_dataset)
        assert response.status_code == 415

    def test_post_yaml_dataset(
        self,
        dataset_url: str,
        example_yaml_dataset,
        test_client: TestClient,
        test_config,
    ) -> None:
        headers = {"Content-type": "application/x-yaml"}
        response = test_client.post(
            dataset_url, headers=headers, data=example_yaml_dataset
        )
        assert response.status_code == 201

        assert response.json()["inserted"] == 1
        assert response.json()["updated"] == 0

        # Post again
        response = test_client.post(
            dataset_url, headers=headers, data=example_yaml_dataset
        )
        assert response.status_code == 200
        assert response.json()["inserted"] == 0
        assert response.json()["updated"] == 1

        _api.delete(
            url=test_config.cli.server_url,
            resource_type="dataset",
            resource_id="postgres_example_test_dataset",
            headers=test_config.user.request_headers,
        )

    def test_post_yaml_dataset_invalid_content(
        self,
        dataset_url: str,
        example_invalid_yaml_dataset,
        test_client: TestClient,
    ) -> None:
        headers = {"Content-type": "application/x-yaml"}
        response = test_client.post(
            dataset_url, headers=headers, data=example_invalid_yaml_dataset
        )
        assert response.status_code == 400

    def test_post_no_datasets(
        self,
        dataset_url: str,
        test_client: TestClient,
    ) -> None:
        headers = {"Content-type": "application/x-yaml"}
        response = test_client.post(dataset_url, headers=headers, data="")
        assert response.status_code == 400
        assert response.json()["detail"] == "No datasets in request body"

    def test_post_multiple_yaml_datasets(
        self,
        dataset_url: str,
        example_yaml_datasets,
        test_client: TestClient,
        test_config,
    ) -> None:
        headers = {"Content-type": "application/x-yaml"}
        response = test_client.post(
            dataset_url, headers=headers, data=example_yaml_datasets
        )
        assert response.status_code == 201
        assert response.json()["inserted"] == 2
        assert response.json()["updated"] == 0

        _api.delete(
            url=test_config.cli.server_url,
            resource_type="dataset",
            resource_id="mssql_example_test_dataset",
            headers=test_config.user.request_headers,
        )
        _api.delete(
            url=test_config.cli.server_url,
            resource_type="dataset",
            resource_id="mariadb_example_test_dataset",
            headers=test_config.user.request_headers,
        )
