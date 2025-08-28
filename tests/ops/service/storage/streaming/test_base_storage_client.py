"""Tests for the BaseStorageClient abstract class."""

from unittest.mock import Mock

import pytest

from fides.api.service.storage.streaming.base_storage_client import \
    BaseStorageClient


class TestBaseStorageClient:
    """Test the BaseStorageClient abstract class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that BaseStorageClient cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseStorageClient({})

    def test_abstract_methods_exist(self):
        """Test that all required abstract methods exist."""
        # Check that the abstract methods are defined
        assert hasattr(BaseStorageClient, "build_uri")
        assert hasattr(BaseStorageClient, "get_transport_params")
        assert hasattr(BaseStorageClient, "generate_presigned_url")

    def test_init_stores_storage_secrets(self):
        """Test that __init__ properly stores storage secrets."""

        # Create a concrete subclass for testing
        class ConcreteStorageClient(BaseStorageClient):
            def build_uri(self, bucket: str, key: str) -> str:
                return f"test://{bucket}/{key}"

            def get_transport_params(self) -> dict:
                return {}

            def generate_presigned_url(self, bucket: str, key: str, ttl_seconds=None):
                return f"https://test.com/{bucket}/{key}"

        secrets = {"test_key": "test_value"}
        client = ConcreteStorageClient(secrets)
        assert client.storage_secrets == secrets
