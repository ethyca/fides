from typing import Generator

import pytest
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_422_UNPROCESSABLE_ENTITY,
)
from starlette.testclient import TestClient

from fides.api.models.sql_models import Dataset as CtlDataset
from fides.common.api.scope_registry import CTL_DATASET_CREATE, CTL_DATASET_READ
from fides.common.api.v1.urn_registry import DATASETS, V1_URL_PREFIX
from tests.conftest import generate_role_header_for_user


class TestCreateDataset:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + DATASETS

    @pytest.fixture(scope="function")
    def dataset_payload(self) -> dict:
        return {
            "fides_key": "test_dataset",
            "name": "Test Dataset",
            "description": "A test dataset",
            "collections": [],
        }

    @pytest.fixture(scope="function")
    def existing_dataset(
        self, db, dataset_payload
    ) -> Generator[CtlDataset, None, None]:
        """Create a dataset in the database"""
        dataset = CtlDataset.create_from_dataset_dict(db, dataset_payload)
        yield dataset
        dataset.delete(db)

    def test_create_dataset_not_authenticated(
        self, api_client: TestClient, url: str, dataset_payload: dict
    ) -> None:
        """Test that creating a dataset without authentication returns a 401 error"""
        response = api_client.post(url, json=dataset_payload)
        assert response.status_code == HTTP_401_UNAUTHORIZED

    def test_create_dataset_wrong_scope(
        self,
        api_client: TestClient,
        generate_auth_header,
        url: str,
        dataset_payload: dict,
    ) -> None:
        """Test that creating a dataset with wrong scope returns a 403 error"""
        auth_header = generate_auth_header(scopes=[CTL_DATASET_READ])
        response = api_client.post(url, headers=auth_header, json=dataset_payload)
        assert response.status_code == HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        "role,expected_status",
        [
            ("owner_user", HTTP_201_CREATED),
            ("contributor_user", HTTP_201_CREATED),
            ("viewer_and_approver_user", HTTP_403_FORBIDDEN),
            ("viewer_user", HTTP_403_FORBIDDEN),
            ("approver_user", HTTP_403_FORBIDDEN),
        ],
    )
    def test_create_dataset_with_role(
        self,
        api_client: TestClient,
        url: str,
        dataset_payload: dict,
        db,
        request,
        role: str,
        expected_status: int,
    ) -> None:
        """Test dataset creation with different user roles"""
        # Use a different dataset key for each test to avoid conflicts
        modified_payload = dataset_payload.copy()
        modified_payload["fides_key"] = f"{dataset_payload['fides_key']}_{role}"
        modified_payload["name"] = f"{dataset_payload['name']} {role}"

        user_role = request.getfixturevalue(role)
        auth_header = generate_role_header_for_user(
            user_role, roles=user_role.permissions.roles
        )

        response = api_client.post(url, headers=auth_header, json=modified_payload)
        assert response.status_code == expected_status

        # Clean up if dataset was created
        if expected_status == HTTP_201_CREATED:
            dataset = (
                db.query(CtlDataset)
                .filter(CtlDataset.fides_key == modified_payload["fides_key"])
                .first()
            )
            if dataset:
                dataset.delete(db)

    @pytest.mark.usefixtures("existing_dataset")
    def test_create_dataset_key_already_exists(
        self,
        api_client: TestClient,
        generate_auth_header,
        url: str,
        dataset_payload: dict,
    ) -> None:
        """Test that creating a dataset with a key that already exists returns a 422 error"""
        auth_header = generate_auth_header(scopes=[CTL_DATASET_CREATE])

        # Try to create a dataset with the same key but different name
        payload = dataset_payload.copy()
        payload["name"] = "Different Name"

        response = api_client.post(url, headers=auth_header, json=payload)

        assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY
        assert (
            response.json()["detail"]
            == 'Dataset with fides_key "test_dataset" already exists.'
        )

    @pytest.mark.usefixtures("existing_dataset")
    def test_create_dataset_name_already_exists(
        self,
        api_client: TestClient,
        generate_auth_header,
        url: str,
        dataset_payload: dict,
    ) -> None:
        """Test that creating a dataset with a name that already exists returns a 422 error"""
        auth_header = generate_auth_header(scopes=[CTL_DATASET_CREATE])

        # Try to create a dataset with the same name but different key
        payload = dataset_payload.copy()
        payload["fides_key"] = "different_key"

        response = api_client.post(url, headers=auth_header, json=payload)

        assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY
        assert (
            response.json()["detail"]
            == 'Dataset with name "Test Dataset" already exists.'
        )

    def test_create_dataset(
        self, api_client: TestClient, generate_auth_header, url: str
    ) -> None:
        """Test that creating a dataset successfully returns a 201 status code"""
        auth_header = generate_auth_header(scopes=[CTL_DATASET_CREATE])

        payload = {
            "fides_key": "new_test_dataset",
            "name": "New Test Dataset",
            "description": "A new test dataset",
            "collections": [],
        }

        response = api_client.post(url, headers=auth_header, json=payload)
        assert response.status_code == HTTP_201_CREATED
