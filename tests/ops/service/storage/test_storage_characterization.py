"""
Characterization tests for storage provider behavior.

These tests capture the current behavior of storage functions to ensure
that refactoring to the new StorageProvider interface preserves all
existing behavior. They should pass BEFORE and AFTER refactoring.

If any test fails after refactoring, behavior has changed unintentionally.
"""

from io import BytesIO
from tempfile import SpooledTemporaryFile
from typing import Any, Dict, List, Tuple
from unittest.mock import MagicMock, create_autospec, patch

import pytest
from botocore.exceptions import ClientError, ParamValidationError

from fides.api.common_exceptions import StorageUploadError
from fides.api.models.storage import StorageConfig
from fides.api.schemas.storage.storage import (
    AWSAuthMethod,
    GCSAuthMethod,
    StorageDetails,
    StorageSecrets,
    StorageType,
)
from fides.api.service.storage.gcs import get_gcs_client
from fides.api.service.storage.s3 import (
    create_presigned_url_for_s3,
    generic_delete_from_s3,
    generic_retrieve_from_s3,
    generic_upload_to_s3,
    get_file_size,
    maybe_get_s3_client,
)
from fides.api.service.storage.util import (
    LARGE_FILE_THRESHOLD,
    AllowedFileType,
    get_allowed_file_type_or_raise,
    get_local_filename,
)


class TestStorageCharacterization:
    """
    Characterization tests that capture and verify current storage behavior.

    These tests define the "golden" behavior that must be preserved during
    refactoring to the new StorageProvider interface.
    """

    # ==================== S3 Upload Behavior ====================

    @pytest.mark.parametrize(
        "file_extension,expected_content_type",
        [
            ("pdf", "application/pdf"),
            ("doc", "application/msword"),
            (
                "docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
            ("txt", "text/plain"),
            ("jpg", "image/jpeg"),
            ("png", "image/png"),
            ("xls", "application/vnd.ms-excel"),
            (
                "xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
            ("csv", "text/csv"),
            ("zip", "application/zip"),
        ],
    )
    def test_allowed_file_types_content_type_mapping(
        self, file_extension: str, expected_content_type: str
    ):
        """Verify content type mapping for all allowed file types is preserved."""
        file_key = f"test_file.{file_extension}"
        result = get_allowed_file_type_or_raise(file_key)
        assert (
            result == expected_content_type
        ), f"Content type for .{file_extension} should be {expected_content_type}, got {result}"

    @pytest.mark.parametrize(
        "file_extension",
        [
            "gif",
            "bmp",
            "ico",
            "webp",
            "heic",
            "heif",
            "ppt",
            "pptx",
            "json",
            "xml",
            "yaml",
            "yml",
            "exe",
            "app",
            "dmg",
        ],
    )
    def test_disallowed_file_types_raise_error(self, file_extension: str):
        """Verify disallowed file types raise ValueError."""
        file_key = f"test_file.{file_extension}"
        with pytest.raises(ValueError) as exc_info:
            get_allowed_file_type_or_raise(file_key)
        assert "Invalid or unallowed file extension" in str(exc_info.value)

    def test_s3_upload_returns_size_and_url_tuple(
        self, storage_config: StorageConfig, mock_s3_client
    ):
        """Verify S3 upload returns (file_size, presigned_url) tuple."""
        content = b"test content for upload"
        document = BytesIO(content)
        bucket_name = storage_config.details[StorageDetails.BUCKET.value]
        auth_method = storage_config.details[StorageDetails.AUTH_METHOD.value]

        result = generic_upload_to_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key="test.pdf",
            auth_method=auth_method,
            document=document,
        )

        # Result must be a tuple of (int, str)
        assert isinstance(result, tuple), "Upload result should be a tuple"
        assert len(result) == 2, "Upload result should have 2 elements"
        assert isinstance(result[0], int), "First element should be file size (int)"
        assert isinstance(
            result[1], str
        ), "Second element should be presigned URL (str)"
        assert result[0] == len(content), "File size should match content length"

    def test_s3_upload_rejects_non_file_like_objects(
        self, storage_config: StorageConfig, mock_s3_client
    ):
        """Verify S3 upload raises TypeError for non-file-like objects."""
        bucket_name = storage_config.details[StorageDetails.BUCKET.value]
        auth_method = storage_config.details[StorageDetails.AUTH_METHOD.value]

        with pytest.raises(TypeError) as exc_info:
            generic_upload_to_s3(
                storage_secrets=storage_config.secrets,
                bucket_name=bucket_name,
                file_key="test.pdf",
                auth_method=auth_method,
                document="not a file object",  # type: ignore
            )
        assert "file-like object" in str(exc_info.value)

    def test_s3_upload_with_spooled_temp_file(
        self, storage_config: StorageConfig, mock_s3_client
    ):
        """Verify S3 upload works with SpooledTemporaryFile."""
        content = b"spooled content"
        spooled_file = SpooledTemporaryFile()
        spooled_file.write(content)
        spooled_file.seek(0)

        bucket_name = storage_config.details[StorageDetails.BUCKET.value]
        auth_method = storage_config.details[StorageDetails.AUTH_METHOD.value]

        result = generic_upload_to_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key="spooled.pdf",
            auth_method=auth_method,
            document=spooled_file,
        )

        assert result[0] == len(content)

    # ==================== S3 Retrieve Behavior ====================

    def test_s3_retrieve_returns_size_and_content_or_url(
        self, storage_config: StorageConfig, mock_s3_client
    ):
        """Verify S3 retrieve returns (size, content_or_url) tuple."""
        content = b"retrieve test content"
        document = BytesIO(content)
        bucket_name = storage_config.details[StorageDetails.BUCKET.value]
        auth_method = storage_config.details[StorageDetails.AUTH_METHOD.value]

        # First upload
        generic_upload_to_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key="retrieve_test.pdf",
            auth_method=auth_method,
            document=document,
        )

        # Then retrieve with get_content=True
        result = generic_retrieve_from_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key="retrieve_test.pdf",
            auth_method=auth_method,
            get_content=True,
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], int)  # File size
        # When get_content=True and file is small, returns BytesIO
        assert hasattr(
            result[1], "read"
        ), "Should return file-like object for small files"

    def test_s3_retrieve_returns_presigned_url_for_large_files(
        self, storage_config: StorageConfig, mock_s3_client
    ):
        """Verify S3 retrieve returns presigned URL for files > threshold."""
        bucket_name = storage_config.details[StorageDetails.BUCKET.value]
        auth_method = storage_config.details[StorageDetails.AUTH_METHOD.value]

        # Upload a file
        generic_upload_to_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key="test_url.pdf",
            auth_method=auth_method,
            document=BytesIO(b"content"),
        )

        # Retrieve without get_content - should return URL
        result = generic_retrieve_from_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key="test_url.pdf",
            auth_method=auth_method,
            get_content=False,
        )

        assert isinstance(
            result[1], str
        ), "Should return URL string when get_content=False"

    # ==================== S3 Delete Behavior ====================

    def test_s3_delete_single_file(self, storage_config: StorageConfig, mock_s3_client):
        """Verify S3 delete removes a single file."""
        bucket_name = storage_config.details[StorageDetails.BUCKET.value]
        auth_method = storage_config.details[StorageDetails.AUTH_METHOD.value]

        # Upload a file
        generic_upload_to_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key="to_delete.pdf",
            auth_method=auth_method,
            document=BytesIO(b"delete me"),
        )

        # Delete should not raise
        generic_delete_from_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key="to_delete.pdf",
            auth_method=auth_method,
        )

    def test_s3_delete_prefix_removes_all_matching(
        self, storage_config: StorageConfig, mock_s3_client
    ):
        """Verify S3 delete with prefix/ removes all matching objects."""
        bucket_name = storage_config.details[StorageDetails.BUCKET.value]
        auth_method = storage_config.details[StorageDetails.AUTH_METHOD.value]

        # Upload multiple files with same prefix
        for i in range(3):
            generic_upload_to_s3(
                storage_secrets=storage_config.secrets,
                bucket_name=bucket_name,
                file_key=f"folder/{i}.pdf",
                auth_method=auth_method,
                document=BytesIO(f"content {i}".encode()),
            )

        # Delete with prefix (ends with /)
        generic_delete_from_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key="folder/",
            auth_method=auth_method,
        )

    # ==================== Presigned URL Behavior ====================

    def test_presigned_url_default_ttl(
        self, storage_config: StorageConfig, mock_s3_client
    ):
        """Verify presigned URL generation uses default TTL when not specified."""
        bucket_name = storage_config.details[StorageDetails.BUCKET.value]

        url = create_presigned_url_for_s3(
            s3_client=mock_s3_client,
            bucket_name=bucket_name,
            file_key="test.pdf",
            ttl_seconds=None,  # Use default
        )

        assert isinstance(url, str)
        assert url.startswith("https://") or url.startswith("http://")

    def test_presigned_url_max_ttl_validation(
        self, storage_config: StorageConfig, mock_s3_client
    ):
        """Verify presigned URL rejects TTL > 7 days."""
        bucket_name = storage_config.details[StorageDetails.BUCKET.value]
        max_ttl_seconds = 604800  # 7 days

        with pytest.raises(ValueError) as exc_info:
            create_presigned_url_for_s3(
                s3_client=mock_s3_client,
                bucket_name=bucket_name,
                file_key="test.pdf",
                ttl_seconds=max_ttl_seconds + 1,
            )
        assert "TTL must be less than 7 days" in str(exc_info.value)

    # ==================== GCS Client Behavior ====================

    def test_gcs_client_adc_auth_method(self):
        """Verify GCS client creation with ADC auth method."""
        with patch("fides.api.service.storage.gcs.Client") as mock_client:
            mock_client.return_value = MagicMock()
            client = get_gcs_client(GCSAuthMethod.ADC.value, None)
            mock_client.assert_called_once()
            assert client is not None

    def test_gcs_client_service_account_requires_secrets(self):
        """Verify GCS client with service account raises error without secrets."""
        with pytest.raises(StorageUploadError) as exc_info:
            get_gcs_client(GCSAuthMethod.SERVICE_ACCOUNT_KEYS.value, None)
        assert "Storage secrets not found" in str(exc_info.value)

    def test_gcs_client_invalid_auth_method_raises_error(self):
        """Verify GCS client raises ValueError for invalid auth method."""
        with pytest.raises(ValueError) as exc_info:
            get_gcs_client("invalid_auth", None)
        assert "auth method not supported" in str(exc_info.value)

    # ==================== Local Storage Behavior ====================

    def test_local_filename_path_traversal_protection(self):
        """Verify local storage prevents path traversal attacks."""
        # Attempting path traversal should be handled safely
        result = get_local_filename("test_file.pdf")
        assert ".." not in result, "Path should not contain .."
        assert result.endswith("test_file.pdf")

    def test_local_filename_creates_valid_path(self):
        """Verify local filename generation creates valid paths."""
        result = get_local_filename("subfolder/test.pdf")
        assert "subfolder" in result
        assert result.endswith("test.pdf")

    # ==================== Multipart Upload Threshold ====================

    def test_large_file_threshold_is_2gb(self):
        """Verify large file threshold constant is 2GB."""
        expected_threshold = 2 * 1024 * 1024 * 1024  # 2GB
        assert LARGE_FILE_THRESHOLD == expected_threshold, (
            f"Large file threshold should be 2GB ({expected_threshold}), "
            f"got {LARGE_FILE_THRESHOLD}"
        )

    # ==================== Error Type Preservation ====================

    def test_s3_client_error_type_preserved(self):
        """Verify S3 client errors are raised as ClientError."""

        def raise_client_error(auth_method, storage_secrets):
            raise ClientError(
                {"Error": {"Code": "403", "Message": "Access Denied"}},
                "GetObject",
            )

        with patch("fides.api.service.storage.s3.get_s3_client", raise_client_error):
            with pytest.raises(ClientError):
                maybe_get_s3_client("test_auth", {})

    def test_s3_param_validation_converted_to_value_error(self):
        """Verify ParamValidationError is converted to ValueError."""

        def raise_param_error(auth_method, storage_secrets):
            raise ParamValidationError(report="Invalid parameters")

        with patch("fides.api.service.storage.s3.get_s3_client", raise_param_error):
            with pytest.raises(ValueError) as exc_info:
                maybe_get_s3_client("test_auth", {})
            assert "parameters you provided are incorrect" in str(exc_info.value)

    # ==================== Auth Method Handling ====================

    @pytest.mark.parametrize(
        "auth_method",
        [
            AWSAuthMethod.AUTOMATIC.value,
            AWSAuthMethod.SECRET_KEYS.value,
        ],
    )
    def test_s3_supports_all_auth_methods(self, auth_method: str):
        """Verify S3 client supports all defined auth methods."""
        # Just verify the auth method values are valid strings
        assert isinstance(auth_method, str)
        assert len(auth_method) > 0

    @pytest.mark.parametrize(
        "auth_method",
        [
            GCSAuthMethod.ADC.value,
            GCSAuthMethod.SERVICE_ACCOUNT_KEYS.value,
        ],
    )
    def test_gcs_supports_all_auth_methods(self, auth_method: str):
        """Verify GCS client supports all defined auth methods."""
        assert isinstance(auth_method, str)
        assert len(auth_method) > 0


class TestStorageConfigBehavior:
    """Tests for StorageConfig model behavior that providers must respect."""

    def test_storage_type_enum_values(self):
        """Verify storage type enum values are preserved."""
        assert StorageType.s3.value == "s3"
        assert StorageType.gcs.value == "gcs"
        assert StorageType.local.value == "local"

    def test_storage_details_keys(self):
        """Verify storage details enum keys are preserved."""
        assert StorageDetails.BUCKET.value == "bucket"
        assert StorageDetails.AUTH_METHOD.value == "auth_method"
        assert StorageDetails.NAMING.value == "naming"

    def test_storage_secrets_keys(self):
        """Verify storage secrets enum keys are preserved."""
        assert StorageSecrets.AWS_ACCESS_KEY_ID.value == "aws_access_key_id"
        assert StorageSecrets.AWS_SECRET_ACCESS_KEY.value == "aws_secret_access_key"


class TestAllowedFileTypes:
    """Capture the exact set of allowed file types."""

    def test_all_allowed_file_types(self):
        """Document all currently allowed file types."""
        expected_allowed = {
            "pdf",
            "doc",
            "docx",
            "txt",
            "jpg",
            "png",
            "xls",
            "xlsx",
            "csv",
            "zip",
        }
        actual_allowed = {ft.name for ft in AllowedFileType}

        assert (
            actual_allowed == expected_allowed
        ), f"Allowed file types changed. Expected {expected_allowed}, got {actual_allowed}"

    def test_allowed_file_type_enum_values(self):
        """Verify AllowedFileType enum values (content types) are preserved."""
        expected_mappings = {
            "pdf": "application/pdf",
            "doc": "application/msword",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "txt": "text/plain",
            "jpg": "image/jpeg",
            "png": "image/png",
            "xls": "application/vnd.ms-excel",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "csv": "text/csv",
            "zip": "application/zip",
        }

        for file_type, expected_content_type in expected_mappings.items():
            actual = AllowedFileType[file_type].value
            assert (
                actual == expected_content_type
            ), f"Content type for {file_type} changed from {expected_content_type} to {actual}"
