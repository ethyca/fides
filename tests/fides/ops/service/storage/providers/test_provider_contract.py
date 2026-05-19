"""
Contract tests for storage providers.

These tests define the behavioral contract that ALL storage providers must satisfy.
Each provider implementation should pass all contract tests to ensure consistent
behavior across different storage backends.

The tests use abstract fixtures that are implemented differently for each provider,
allowing the same test logic to run against S3, GCS, and Local implementations.
"""

from abc import ABC, abstractmethod
from io import BytesIO
from typing import Any
from uuid import uuid4

import pytest

from fides.api.service.storage.providers.base import (
    ObjectInfo,
    StorageProvider,
    UploadResult,
)


class StorageProviderContractTest(ABC):
    """Abstract base class for storage provider contract tests.

    All storage providers must pass these tests to ensure behavioral
    compatibility. Subclass this for each provider implementation.
    """

    @pytest.fixture
    @abstractmethod
    def provider(self) -> StorageProvider:
        """Return a configured provider instance for testing."""

    @pytest.fixture
    @abstractmethod
    def bucket(self) -> str:
        """Return a test bucket name."""

    @pytest.fixture
    def unique_key(self) -> str:
        """Generate a unique key for each test."""
        return f"test-{uuid4()}.pdf"

    @pytest.fixture
    def test_content(self) -> bytes:
        """Sample content for testing."""
        return b"Test content for contract verification"

    # ==================== Upload Contract ====================

    def test_upload_returns_upload_result(
        self,
        provider: StorageProvider,
        bucket: str,
        unique_key: str,
        test_content: bytes,
    ):
        """Upload must return an UploadResult instance."""
        result = provider.upload(bucket, unique_key, BytesIO(test_content))

        assert isinstance(result, UploadResult), "Upload must return UploadResult"

    def test_upload_result_has_file_size(
        self,
        provider: StorageProvider,
        bucket: str,
        unique_key: str,
        test_content: bytes,
    ):
        """UploadResult must contain accurate file size."""
        result = provider.upload(bucket, unique_key, BytesIO(test_content))

        assert result.file_size == len(test_content), (
            f"File size should be {len(test_content)}, got {result.file_size}"
        )

    def test_upload_accepts_bytesio(
        self,
        provider: StorageProvider,
        bucket: str,
        unique_key: str,
        test_content: bytes,
    ):
        """Upload must accept BytesIO objects."""
        data = BytesIO(test_content)
        result = provider.upload(bucket, unique_key, data)

        assert result.file_size > 0

    def test_upload_rejects_non_file_like(
        self, provider: StorageProvider, bucket: str, unique_key: str
    ):
        """Upload must reject non-file-like objects."""
        with pytest.raises(TypeError):
            provider.upload(bucket, unique_key, "not a file")  # type: ignore

    # ==================== Download Contract ====================

    def test_download_returns_file_like_object(
        self,
        provider: StorageProvider,
        bucket: str,
        unique_key: str,
        test_content: bytes,
    ):
        """Download must return a file-like object with read()."""
        provider.upload(bucket, unique_key, BytesIO(test_content))

        downloaded = provider.download(bucket, unique_key)

        assert hasattr(downloaded, "read"), "Download must return file-like object"

    def test_download_content_matches_upload(
        self,
        provider: StorageProvider,
        bucket: str,
        unique_key: str,
        test_content: bytes,
    ):
        """Downloaded content must match uploaded content."""
        provider.upload(bucket, unique_key, BytesIO(test_content))

        downloaded = provider.download(bucket, unique_key)
        content = downloaded.read()

        assert content == test_content, "Downloaded content must match uploaded"

    # ==================== Delete Contract ====================

    def test_delete_does_not_raise_for_existing(
        self,
        provider: StorageProvider,
        bucket: str,
        unique_key: str,
        test_content: bytes,
    ):
        """Delete must not raise for existing objects."""
        provider.upload(bucket, unique_key, BytesIO(test_content))

        # Should not raise
        provider.delete(bucket, unique_key)

    def test_delete_makes_object_not_exist(
        self,
        provider: StorageProvider,
        bucket: str,
        unique_key: str,
        test_content: bytes,
    ):
        """Delete must make object no longer exist."""
        provider.upload(bucket, unique_key, BytesIO(test_content))
        provider.delete(bucket, unique_key)

        assert not provider.exists(bucket, unique_key)

    # ==================== Exists Contract ====================

    def test_exists_returns_true_for_existing(
        self,
        provider: StorageProvider,
        bucket: str,
        unique_key: str,
        test_content: bytes,
    ):
        """Exists must return True for uploaded objects."""
        provider.upload(bucket, unique_key, BytesIO(test_content))

        assert provider.exists(bucket, unique_key) is True

    def test_exists_returns_false_for_nonexistent(
        self, provider: StorageProvider, bucket: str
    ):
        """Exists must return False for non-existent objects."""
        nonexistent_key = f"does-not-exist-{uuid4()}.txt"

        assert provider.exists(bucket, nonexistent_key) is False

    # ==================== Presigned URL Contract ====================

    def test_presigned_url_returns_string(
        self,
        provider: StorageProvider,
        bucket: str,
        unique_key: str,
        test_content: bytes,
    ):
        """Presigned URL must return a string."""
        provider.upload(bucket, unique_key, BytesIO(test_content))

        url = provider.generate_presigned_url(bucket, unique_key)

        assert isinstance(url, str), "Presigned URL must be a string"
        assert len(url) > 0, "Presigned URL must not be empty"

    def test_presigned_url_starts_with_valid_prefix(
        self,
        provider: StorageProvider,
        bucket: str,
        unique_key: str,
        test_content: bytes,
    ):
        """Presigned URL must start with http://, https://, or / (local path)."""
        provider.upload(bucket, unique_key, BytesIO(test_content))

        url = provider.generate_presigned_url(bucket, unique_key)

        valid_prefixes = ("http://", "https://", "/", "fides_uploads")
        assert any(url.startswith(prefix) for prefix in valid_prefixes), (
            f"Presigned URL must start with one of {valid_prefixes}, got {url[:50]}"
        )

    # ==================== File Size Contract ====================

    def test_get_file_size_returns_correct_size(
        self,
        provider: StorageProvider,
        bucket: str,
        unique_key: str,
        test_content: bytes,
    ):
        """Get file size must return accurate size."""
        provider.upload(bucket, unique_key, BytesIO(test_content))

        size = provider.get_file_size(bucket, unique_key)

        assert size == len(test_content), (
            f"File size should be {len(test_content)}, got {size}"
        )


class TestLocalProviderContract(StorageProviderContractTest):
    """Contract tests for LocalStorageProvider."""

    @pytest.fixture
    def provider(self, local_provider) -> StorageProvider:
        """Return configured LocalStorageProvider."""
        return local_provider

    @pytest.fixture
    def bucket(self) -> str:
        """Bucket is ignored for local storage."""
        return ""


class TestS3ProviderContractMocked(StorageProviderContractTest):
    """Contract tests for S3StorageProvider with mocked AWS calls.

    These tests verify the provider contract using mocked S3 functions.
    For real S3 integration tests, see the integration test suite.
    """

    @pytest.fixture
    def provider(self, s3_provider_mock) -> StorageProvider:
        """Return mocked S3StorageProvider."""
        return s3_provider_mock

    @pytest.fixture
    def bucket(self) -> str:
        """Return test bucket name."""
        return "test-bucket"

    # Override tests that don't work with mocks
    def test_download_content_matches_upload(
        self,
        provider: StorageProvider,
        bucket: str,
        unique_key: str,
        test_content: bytes,
    ):
        """Skip for mocked provider - content roundtrip not testable with mocks."""
        pytest.skip("Content roundtrip not testable with mocked S3")

    def test_delete_makes_object_not_exist(
        self,
        provider: StorageProvider,
        bucket: str,
        unique_key: str,
        test_content: bytes,
    ):
        """Skip for mocked provider - state changes not tracked in mocks."""
        pytest.skip("State changes not tracked in mocked S3")

    def test_exists_returns_true_for_existing(
        self,
        provider: StorageProvider,
        bucket: str,
        unique_key: str,
        test_content: bytes,
    ):
        """Skip for mocked provider - existence check not testable with mocks."""
        pytest.skip("Existence not testable with mocked S3")

    def test_upload_result_has_file_size(
        self,
        provider: StorageProvider,
        bucket: str,
        unique_key: str,
        test_content: bytes,
    ):
        """Skip for mocked provider - file size is hardcoded in mock."""
        pytest.skip("File size hardcoded in mocked S3")

    def test_upload_rejects_non_file_like(
        self, provider: StorageProvider, bucket: str, unique_key: str
    ):
        """Skip for mocked provider - mock doesn't validate input types."""
        pytest.skip("Input validation not testable with mocked S3")

    def test_exists_returns_false_for_nonexistent(
        self, provider: StorageProvider, bucket: str
    ):
        """Skip for mocked provider - mock returns hardcoded value."""
        pytest.skip("Existence not testable with mocked S3")

    def test_get_file_size_returns_correct_size(
        self,
        provider: StorageProvider,
        bucket: str,
        unique_key: str,
        test_content: bytes,
    ):
        """Skip for mocked provider - file size is hardcoded in mock."""
        pytest.skip("File size hardcoded in mocked S3")


class TestGCSProviderContractMocked(StorageProviderContractTest):
    """Contract tests for GCSStorageProvider with mocked GCP calls.

    These tests verify the provider contract using mocked GCS functions.
    For real GCS integration tests, see the integration test suite.
    """

    @pytest.fixture
    def provider(self, gcs_provider_mock) -> StorageProvider:
        """Return mocked GCSStorageProvider."""
        return gcs_provider_mock

    @pytest.fixture
    def bucket(self) -> str:
        """Return test bucket name."""
        return "test-bucket"

    # Override tests that don't work with mocks
    def test_download_content_matches_upload(
        self,
        provider: StorageProvider,
        bucket: str,
        unique_key: str,
        test_content: bytes,
    ):
        """Skip for mocked provider - content roundtrip not testable with mocks."""
        pytest.skip("Content roundtrip not testable with mocked GCS")

    def test_delete_makes_object_not_exist(
        self,
        provider: StorageProvider,
        bucket: str,
        unique_key: str,
        test_content: bytes,
    ):
        """Skip for mocked provider - state changes not tracked in mocks."""
        pytest.skip("State changes not tracked in mocked GCS")

    def test_get_file_size_returns_correct_size(
        self,
        provider: StorageProvider,
        bucket: str,
        unique_key: str,
        test_content: bytes,
    ):
        """Skip for mocked provider - size is hardcoded in mock."""
        pytest.skip("File size hardcoded in mocked GCS")

    def test_exists_returns_false_for_nonexistent(
        self, provider: StorageProvider, bucket: str
    ):
        """Skip for mocked provider - mock returns hardcoded value."""
        pytest.skip("Existence not testable with mocked GCS")
