from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fides.api.models.sql_models import Dataset as CtlDataset
from fides.common.api.scope_registry import CTL_DATASET_READ


@pytest.fixture
def minimal_dataset(db: Session) -> Generator[CtlDataset, None, None]:
    """Create a minimal test dataset and clean up after test"""
    dataset = CtlDataset(
        fides_key="test_dataset",
        name="Test Dataset",
        organization_fides_key="default_organization",
        collections=[],
    )
    db.add(dataset)
    db.commit()
    yield dataset

    # Cleanup
    db.delete(dataset)
    db.commit()


@pytest.fixture
def search_datasets(db: Session) -> Generator[list[CtlDataset], None, None]:
    """Create test datasets for search and pagination tests and clean up after test"""
    datasets = [
        CtlDataset(
            fides_key="test_dataset_1",
            name="Test Dataset One",
            organization_fides_key="default_organization",
            collections=[],
        ),
        CtlDataset(
            fides_key="test_dataset_2",
            name="Another Dataset",
            organization_fides_key="default_organization",
            collections=[],
        ),
    ]
    for dataset in datasets:
        db.add(dataset)
    db.commit()
    yield datasets

    # Cleanup
    for dataset in datasets:
        db.delete(dataset)
    db.commit()


@pytest.fixture
def connection_type_datasets(db: Session) -> Generator[list[CtlDataset], None, None]:
    """Create test datasets with different connection types and clean up after test"""
    datasets = [
        CtlDataset(
            fides_key="bigquery_dataset",
            name="BigQuery Dataset",
            organization_fides_key="default_organization",
            fides_meta={"namespace": {"connection_type": "bigquery"}},
            collections=[],
        ),
        CtlDataset(
            fides_key="postgres_dataset",
            name="Postgres Dataset",
            organization_fides_key="default_organization",
            fides_meta={"namespace": {"connection_type": "postgres"}},
            collections=[],
        ),
        CtlDataset(
            fides_key="mysql_dataset",
            name="MySQL Dataset",
            organization_fides_key="default_organization",
            fides_meta={"namespace": {"connection_type": "mysql"}},
            collections=[],
        ),
        CtlDataset(
            fides_key="missing_connection_type_dataset",
            name="Missing Connection Type Dataset",
            organization_fides_key="default_organization",
            collections=[],
        ),
        CtlDataset(
            fides_key="missing_namespace_dataset",
            name="Missing Namespace Dataset",
            organization_fides_key="default_organization",
            collections=[],
            fides_meta={},
        ),
        CtlDataset(
            fides_key="missing_namespace_connection_type_dataset",
            name="Missing Namespace and Connection Type Dataset",
            organization_fides_key="default_organization",
            collections=[],
            fides_meta={"namespace": {}},
        ),
    ]
    for dataset in datasets:
        db.add(dataset)
    db.commit()
    yield datasets

    # Cleanup
    for dataset in datasets:
        db.delete(dataset)
    db.commit()


class TestGenericOverrides:
    def test_list_dataset_paginated_minimal(
        self,
        api_client: TestClient,
        minimal_dataset: CtlDataset,
        generate_auth_header,
    ):
        """Test the minimal parameter in list_dataset_paginated"""
        auth_header = generate_auth_header([CTL_DATASET_READ])

        # Test minimal=True
        response = api_client.get("/api/v1/dataset?minimal=true", headers=auth_header)
        assert response.status_code == 200
        data = response.json()

        # Verify minimal fields are present and non-minimal fields are absent
        assert len(data) > 0
        item = data[0]
        assert "fides_key" in item
        assert "name" in item
        assert item["collections"] is None

        # Test minimal=False
        response = api_client.get("/api/v1/dataset?minimal=false", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        item = data[0]
        assert item["collections"] is not None

    def test_list_dataset_paginated_filters(
        self,
        api_client: TestClient,
        search_datasets: list[CtlDataset],
        generate_auth_header,
    ):
        """Test the filters in list_dataset_paginated"""
        auth_header = generate_auth_header([CTL_DATASET_READ])

        # Test search filter
        response = api_client.get("/api/v1/dataset?search=Another", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Another Dataset"

        # Test pagination
        response = api_client.get("/api/v1/dataset?page=1&size=1", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] > 1

    def test_list_dataset_paginated_connection_type(
        self,
        api_client: TestClient,
        connection_type_datasets: list[CtlDataset],
        generate_auth_header,
    ):
        """Test filtering datasets by connection_type"""
        auth_header = generate_auth_header([CTL_DATASET_READ])

        # Test not filtering by connection type
        response = api_client.get("/api/v1/dataset", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        dataset_keys = [item["fides_key"] for item in data]
        assert "bigquery_dataset" in dataset_keys
        assert "postgres_dataset" in dataset_keys
        assert "mysql_dataset" in dataset_keys
        assert "missing_connection_type_dataset" in dataset_keys
        assert "missing_namespace_dataset" in dataset_keys
        assert "missing_namespace_connection_type_dataset" in dataset_keys

        # Test filtering by bigquery connection type
        response = api_client.get(
            "/api/v1/dataset?connection_type=bigquery", headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        dataset_keys = [item["fides_key"] for item in data]
        assert "bigquery_dataset" in dataset_keys
        assert "postgres_dataset" not in dataset_keys
        assert "mysql_dataset" not in dataset_keys
        assert "missing_connection_type_dataset" not in dataset_keys
        assert "missing_namespace_dataset" not in dataset_keys
        assert "missing_namespace_connection_type_dataset" not in dataset_keys

        # Test filtering by postgres connection type
        response = api_client.get(
            "/api/v1/dataset?connection_type=postgres", headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        dataset_keys = [item["fides_key"] for item in data]
        assert "bigquery_dataset" not in dataset_keys
        assert "postgres_dataset" in dataset_keys
        assert "mysql_dataset" not in dataset_keys
        assert "missing_connection_type_dataset" not in dataset_keys
        assert "missing_namespace_dataset" not in dataset_keys
        assert "missing_namespace_connection_type_dataset" not in dataset_keys

        # Test filtering by mysql connection type
        response = api_client.get(
            "/api/v1/dataset?connection_type=mysql", headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        dataset_keys = [item["fides_key"] for item in data]
        assert "bigquery_dataset" not in dataset_keys
        assert "postgres_dataset" not in dataset_keys
        assert "mysql_dataset" in dataset_keys
        assert "missing_connection_type_dataset" not in dataset_keys
        assert "missing_namespace_dataset" not in dataset_keys
        assert "missing_namespace_connection_type_dataset" not in dataset_keys

        # Test with invalid connection type
        response = api_client.get(
            "/api/v1/dataset?connection_type=invalid", headers=auth_header
        )
        assert (
            response.status_code == 422
        )  # Unprocessable Entity for invalid enum value
