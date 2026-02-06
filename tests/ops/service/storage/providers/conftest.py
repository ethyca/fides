"""Shared fixtures for storage provider tests."""

from contextlib import ExitStack
from io import BytesIO
from typing import Generator
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from fides.api.models.storage import StorageConfig
from fides.api.schemas.storage.storage import (
    AWSAuthMethod,
    FileNaming,
    GCSAuthMethod,
    ResponseFormat,
    StorageDetails,
    StorageSecrets,
    StorageType,
)
from fides.api.service.storage.providers import (
    GCSStorageProvider,
    LocalStorageProvider,
    S3StorageProvider,
    StorageProviderFactory,
)


@pytest.fixture
def test_content() -> bytes:
    """Sample content for upload tests."""
    return b"This is test content for storage provider tests."


@pytest.fixture
def test_file(test_content: bytes) -> BytesIO:
    """File-like object for upload tests."""
    return BytesIO(test_content)


@pytest.fixture
def test_bucket() -> str:
    """Test bucket name."""
    return "test-bucket"


@pytest.fixture
def test_key() -> str:
    """Test object key."""
    return f"test-{uuid4()}.pdf"


@pytest.fixture
def local_provider(tmp_path) -> Generator[LocalStorageProvider, None, None]:
    """Create a LocalStorageProvider for testing.

    Uses a temporary directory that is cleaned up after the test.
    """
    with ExitStack() as stack:
        # Patch the upload directory constants to use tmp_path
        stack.enter_context(
            patch(
                "fides.api.service.storage.providers.local_provider.LOCAL_FIDES_UPLOAD_DIRECTORY",
                str(tmp_path),
            )
        )
        stack.enter_context(
            patch(
                "fides.api.service.storage.util.LOCAL_FIDES_UPLOAD_DIRECTORY",
                str(tmp_path),
            )
        )

        provider = LocalStorageProvider(base_path=str(tmp_path))
        yield provider


@pytest.fixture
def s3_provider_mock() -> Generator[S3StorageProvider, None, None]:
    """Create a mocked S3StorageProvider for testing.

    This fixture mocks the underlying S3 functions to avoid actual AWS calls.
    """
    s3_module = "fides.api.service.storage.providers.s3_provider"

    with ExitStack() as stack:
        # Patch all S3 functions at once
        mock_upload = stack.enter_context(patch(f"{s3_module}.generic_upload_to_s3"))
        mock_retrieve = stack.enter_context(
            patch(f"{s3_module}.generic_retrieve_from_s3")
        )
        mock_delete = stack.enter_context(patch(f"{s3_module}.generic_delete_from_s3"))
        mock_client = stack.enter_context(patch(f"{s3_module}.maybe_get_s3_client"))
        mock_url = stack.enter_context(
            patch(f"{s3_module}.create_presigned_url_for_s3")
        )
        mock_size = stack.enter_context(patch(f"{s3_module}.get_file_size"))

        # Configure mocks
        mock_upload.return_value = (100, "https://presigned-url")
        mock_retrieve.return_value = (100, BytesIO(b"downloaded content"))
        mock_url.return_value = "https://presigned-url"
        mock_size.return_value = 100
        mock_client.return_value = MagicMock()

        provider = S3StorageProvider(
            auth_method=AWSAuthMethod.SECRET_KEYS.value,
            secrets={
                "aws_access_key_id": "test-key",
                "aws_secret_access_key": "test-secret",
            },
        )

        # Attach mocks for inspection
        provider._mock_upload = mock_upload
        provider._mock_retrieve = mock_retrieve
        provider._mock_delete = mock_delete
        provider._mock_client = mock_client
        provider._mock_url = mock_url
        provider._mock_size = mock_size

        yield provider


@pytest.fixture
def gcs_provider_mock() -> Generator[GCSStorageProvider, None, None]:
    """Create a mocked GCSStorageProvider for testing.

    This fixture mocks the GCS client to avoid actual GCP calls.
    """
    with patch(
        "fides.api.service.storage.providers.gcs_provider.get_gcs_client"
    ) as mock_get_client:
        # Create mock client, bucket, and blob
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()

        mock_get_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.list_blobs.return_value = []

        # Configure blob mock
        mock_blob.size = 100
        mock_blob.etag = "test-etag"
        mock_blob.exists.return_value = True
        mock_blob.generate_signed_url.return_value = "https://signed-url"

        provider = GCSStorageProvider(
            auth_method=GCSAuthMethod.ADC.value,
            secrets=None,
        )

        # Attach mocks for inspection
        provider._mock_client = mock_client
        provider._mock_bucket = mock_bucket
        provider._mock_blob = mock_blob

        yield provider
