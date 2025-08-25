"""Tests for the StorageClientFactory class."""

import pytest

from fides.api.schemas.storage.storage import StorageSecrets
from fides.api.service.storage.streaming.s3.s3_storage_client import S3StorageClient
from fides.api.service.storage.streaming.storage_client_factory import (
    StorageClientFactory,
)


class TestStorageClientFactory:
    """Test the StorageClientFactory class."""

    def test_create_s3_client(self):
        """Test creating an S3 storage client."""
        secrets = {StorageSecrets.AWS_ACCESS_KEY_ID: "test_key"}
        client = StorageClientFactory.create_client("s3", secrets)

        assert isinstance(client, S3StorageClient)
        assert client.storage_secrets == secrets

    def test_create_client_case_insensitive(self):
        """Test that storage type is case insensitive."""
        secrets = {StorageSecrets.AWS_ACCESS_KEY_ID: "test_key"}

        # Test uppercase
        client_upper = StorageClientFactory.create_client("S3", secrets)
        assert isinstance(client_upper, S3StorageClient)

        # Test mixed case
        client_mixed = StorageClientFactory.create_client("S3", secrets)
        assert isinstance(client_mixed, S3StorageClient)

    def test_create_client_unsupported_type(self):
        """Test that unsupported storage type raises ValueError."""
        secrets = {}

        with pytest.raises(ValueError, match="Unsupported storage type: invalid"):
            StorageClientFactory.create_client("invalid", secrets)

    def test_normalize_storage_type_s3(self):
        """Test S3 storage type normalization."""
        assert StorageClientFactory._normalize_storage_type("s3") == "s3"
        assert StorageClientFactory._normalize_storage_type("S3") == "s3"
        assert StorageClientFactory._normalize_storage_type("S3") == "s3"

    def test_normalize_storage_type_gcs(self):
        """Test GCS storage type normalization."""
        assert StorageClientFactory._normalize_storage_type("gcs") == "gcs"
        assert StorageClientFactory._normalize_storage_type("gcp") == "gcs"
        assert StorageClientFactory._normalize_storage_type("google") == "gcs"
        assert StorageClientFactory._normalize_storage_type("GCS") == "gcs"
        assert StorageClientFactory._normalize_storage_type("GCP") == "gcs"
        assert StorageClientFactory._normalize_storage_type("GOOGLE") == "gcs"

    def test_normalize_storage_type_unknown(self):
        """Test unknown storage type normalization."""
        assert StorageClientFactory._normalize_storage_type("unknown") == "unknown"
