"""Tests for StorageProviderFactory."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fides.api.models.storage import StorageConfig
from fides.api.schemas.storage.storage import (
    AWSAuthMethod,
    FileNaming,
    GCSAuthMethod,
    ResponseFormat,
    StorageDetails,
    StorageType,
)
from fides.api.service.storage.providers import (
    GCSStorageProvider,
    LocalStorageProvider,
    S3StorageProvider,
    StorageProviderFactory,
)


class TestStorageProviderFactory:
    """Tests for the StorageProviderFactory."""

    def test_create_s3_provider_from_type(self):
        """Factory creates S3StorageProvider for s3 type."""
        provider = StorageProviderFactory.create_from_type(
            storage_type=StorageType.s3,
            details={
                StorageDetails.AUTH_METHOD.value: AWSAuthMethod.SECRET_KEYS.value,
                StorageDetails.BUCKET.value: "test-bucket",
            },
            secrets={
                "aws_access_key_id": "test-key",
                "aws_secret_access_key": "test-secret",
            },
        )

        assert isinstance(provider, S3StorageProvider)

    def test_create_gcs_provider_from_type(self):
        """Factory creates GCSStorageProvider for gcs type."""
        provider = StorageProviderFactory.create_from_type(
            storage_type=StorageType.gcs,
            details={
                StorageDetails.AUTH_METHOD.value: GCSAuthMethod.ADC.value,
                StorageDetails.BUCKET.value: "test-bucket",
            },
            secrets=None,
        )

        assert isinstance(provider, GCSStorageProvider)

    def test_create_local_provider_from_type(self):
        """Factory creates LocalStorageProvider for local type."""
        provider = StorageProviderFactory.create_from_type(
            storage_type=StorageType.local,
            details={},
            secrets=None,
        )

        assert isinstance(provider, LocalStorageProvider)

    def test_create_s3_provider_requires_auth_method(self):
        """Factory raises ValueError if auth_method is missing for S3."""
        with pytest.raises(ValueError) as exc_info:
            StorageProviderFactory.create_from_type(
                storage_type=StorageType.s3,
                details={StorageDetails.BUCKET.value: "test-bucket"},
                secrets=None,
            )

        assert "auth_method is required" in str(exc_info.value)

    def test_create_gcs_provider_requires_auth_method(self):
        """Factory raises ValueError if auth_method is missing for GCS."""
        with pytest.raises(ValueError) as exc_info:
            StorageProviderFactory.create_from_type(
                storage_type=StorageType.gcs,
                details={StorageDetails.BUCKET.value: "test-bucket"},
                secrets=None,
            )

        assert "auth_method is required" in str(exc_info.value)

    def test_create_raises_for_unsupported_type(self):
        """Factory raises ValueError for unsupported storage types."""
        with pytest.raises(ValueError) as exc_info:
            StorageProviderFactory.create_from_type(
                storage_type="unsupported",  # type: ignore
                details={},
                secrets=None,
            )

        assert "Unsupported storage type" in str(exc_info.value)

    def test_create_from_storage_config(self, db: Session):
        """Factory creates provider from StorageConfig model."""
        config = StorageConfig.create(
            db=db,
            data={
                "name": f"test-config-{uuid4()}",
                "type": StorageType.s3,
                "details": {
                    StorageDetails.AUTH_METHOD.value: AWSAuthMethod.SECRET_KEYS.value,
                    StorageDetails.BUCKET.value: "test-bucket",
                    StorageDetails.NAMING.value: FileNaming.request_id.value,
                },
                "format": ResponseFormat.json,
            },
        )
        config.set_secrets(
            db=db,
            storage_secrets={
                "aws_access_key_id": "test-key",
                "aws_secret_access_key": "test-secret",
            },
        )

        try:
            provider = StorageProviderFactory.create(config)
            assert isinstance(provider, S3StorageProvider)
        finally:
            config.delete(db)

    def test_create_local_from_storage_config(self, db: Session):
        """Factory creates LocalStorageProvider from StorageConfig."""
        config = StorageConfig.create(
            db=db,
            data={
                "name": f"test-config-local-{uuid4()}",
                "type": StorageType.local,
                "details": {
                    StorageDetails.NAMING.value: FileNaming.request_id.value,
                },
                "format": ResponseFormat.json,
            },
        )

        try:
            provider = StorageProviderFactory.create(config)
            assert isinstance(provider, LocalStorageProvider)
        finally:
            config.delete(db)

    def test_get_bucket_from_config_s3(self, db: Session):
        """get_bucket_from_config returns bucket for S3."""
        config = StorageConfig.create(
            db=db,
            data={
                "name": f"test-config-bucket-{uuid4()}",
                "type": StorageType.s3,
                "details": {
                    StorageDetails.AUTH_METHOD.value: AWSAuthMethod.SECRET_KEYS.value,
                    StorageDetails.BUCKET.value: "my-test-bucket",
                    StorageDetails.NAMING.value: FileNaming.request_id.value,
                },
                "format": ResponseFormat.json,
            },
        )

        try:
            bucket = StorageProviderFactory.get_bucket_from_config(config)
            assert bucket == "my-test-bucket"
        finally:
            config.delete(db)

    def test_get_bucket_from_config_local(self, db: Session):
        """get_bucket_from_config returns empty string for local."""
        config = StorageConfig.create(
            db=db,
            data={
                "name": f"test-config-bucket-local-{uuid4()}",
                "type": StorageType.local,
                "details": {
                    StorageDetails.NAMING.value: FileNaming.request_id.value,
                },
                "format": ResponseFormat.json,
            },
        )

        try:
            bucket = StorageProviderFactory.get_bucket_from_config(config)
            assert bucket == ""
        finally:
            config.delete(db)

    def test_create_from_string_storage_type(self):
        """Factory accepts string storage type."""
        provider = StorageProviderFactory.create_from_type(
            storage_type="local",  # type: ignore - string instead of enum
            details={},
            secrets=None,
        )

        assert isinstance(provider, LocalStorageProvider)
