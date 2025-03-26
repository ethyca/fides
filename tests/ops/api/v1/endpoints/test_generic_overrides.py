import json
from typing import List

import pytest
from starlette.testclient import TestClient

from fides.common.api.scope_registry import CTL_DATASET_CREATE, CTL_DATASET_READ
from fides.common.api.v1.urn_registry import V1_URL_PREFIX


class TestStandaloneDatasetValidate:
    @pytest.fixture
    def validate_dataset_url(self) -> str:
        return f"{V1_URL_PREFIX}/dataset/validate"

    def test_post_validate_dataset_not_authenticated(
        self, example_datasets: List, validate_dataset_url: str, api_client
    ) -> None:
        response = api_client.post(
            validate_dataset_url, headers={}, json=example_datasets[0]
        )
        assert response.status_code == 401

    def test_post_validate_dataset_wrong_scope(
        self,
        example_datasets: List,
        validate_dataset_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CTL_DATASET_CREATE])
        response = api_client.post(
            validate_dataset_url, headers=auth_header, json=example_datasets[0]
        )
        assert response.status_code == 403

    def test_post_validate_dataset_success(
        self,
        example_datasets: List,
        validate_dataset_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CTL_DATASET_READ])
        response = api_client.post(
            validate_dataset_url, headers=auth_header, json=example_datasets[0]
        )
        assert response.status_code == 200
        response_data = json.loads(response.text)
        assert "dataset" in response_data
        assert "traversal_details" in response_data
        # No connection config, so traversability should be unknown
        assert (
            response_data["traversal_details"] is None
            or response_data["traversal_details"]["is_traversable"] is None
        )

    def test_post_validate_dataset_missing_key(
        self,
        example_datasets: List,
        validate_dataset_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CTL_DATASET_READ])
        invalid_dataset = example_datasets[0].copy()
        invalid_dataset.pop("fides_key", None)
        response = api_client.post(
            validate_dataset_url, headers=auth_header, json=invalid_dataset
        )
        assert response.status_code == 422
        details = json.loads(response.text)["detail"]
        assert any("fides_key" in str(e["loc"]) for e in details)
