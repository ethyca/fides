import pytest
from fastapi import status

from fides.common.api.scope_registry import CTL_DATASET_READ


@pytest.mark.integration
class TestPartitioningEndpoints:
    """Test partitioning endpoint validation."""

    def test_verify_dataset_partitioning_same_fields_success(
        self, test_client, generate_auth_header
    ):
        """Test that partitions with the same field names pass validation."""
        auth_header = generate_auth_header(scopes=[CTL_DATASET_READ])
        partitions = [
            {
                "field": "created_at",
                "start": "2024-01-01",
                "end": "2024-01-15",
                "interval": "7 days",
            },
            {
                "field": "created_at",  # Same field
                "start": "2024-01-16",
                "end": "2024-01-31",
                "interval": "7 days",
            },
        ]

        response = test_client.post(
            "/api/v1/dataset/partitions/verify",
            json=partitions,
            headers=auth_header,
        )

        assert response.status_code == status.HTTP_200_OK
        clauses = response.json()
        assert len(clauses) == 5  # Should return 5 WHERE clauses based on the intervals

    def test_verify_dataset_partitioning_different_fields_error(
        self, test_client, generate_auth_header
    ):
        """Test that partitions with different field names fail validation."""
        auth_header = generate_auth_header(scopes=[CTL_DATASET_READ])
        partitions = [
            {
                "field": "created_at",
                "start": "2024-01-01",
                "end": "2024-01-15",
                "interval": "7 days",
            },
            {
                "field": "updated_at",  # Different field
                "start": "2024-01-16",
                "end": "2024-01-31",
                "interval": "7 days",
            },
        ]

        response = test_client.post(
            "/api/v1/dataset/partitions/verify",
            json=partitions,
            headers=auth_header,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert (
            "All partitioning specifications must use the same field"
            in response.json()["detail"]
        )

    def test_verify_dataset_partitioning_single_partition_success(
        self, test_client, generate_auth_header
    ):
        """Test that single partition passes validation."""
        auth_header = generate_auth_header(scopes=[CTL_DATASET_READ])
        partitions = [
            {
                "field": "created_at",
                "start": "2024-01-01",
                "end": "2024-01-15",
                "interval": "7 days",
            }
        ]

        response = test_client.post(
            "/api/v1/dataset/partitions/verify",
            json=partitions,
            headers=auth_header,
        )

        assert response.status_code == status.HTTP_200_OK
        clauses = response.json()
        assert len(clauses) == 2  # Should return 2 WHERE clauses
