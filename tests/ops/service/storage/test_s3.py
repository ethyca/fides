from io import BytesIO
from tempfile import SpooledTemporaryFile

import boto3
import pytest
from botocore.exceptions import ClientError, ParamValidationError
from moto import mock_aws
from pytest import param

from fides.api.models.storage import StorageConfig
from fides.api.schemas.storage.storage import StorageDetails
from fides.api.service.storage.s3 import (
    generic_delete_from_s3,
    generic_retrieve_from_s3,
    generic_upload_to_s3,
    maybe_get_s3_client,
)
from fides.api.service.storage.util import ALLOWED_FILE_TYPES, LARGE_FILE_THRESHOLD

TEST_DOCUMENT = b"This is a test document."
TEST_SPOOLED_DOC = SpooledTemporaryFile()

NON_ALLOWED_FILE_TYPES = [
    "gif",
    "bmp",
    "ico",
    "webp",
    "heic",
    "heif",
    "hevc",
    "ppt",
    "pptx",
    "json",
    "xml",
    "yaml",
    "yml",
    "toml",
    "tar",
    "gz",
    "bz2",
    "rar",
    "7z",
    "iso",
    "dmg",
    "pkg",
    "deb",
    "rpm",
    "exe",
    "app",
]

FILE_TYPES = NON_ALLOWED_FILE_TYPES + list(ALLOWED_FILE_TYPES.keys())


@pytest.fixture
def test_document():
    return BytesIO(TEST_DOCUMENT)


@pytest.fixture
def bucket_name(storage_config: StorageConfig):
    return storage_config.details[StorageDetails.BUCKET.value]


@pytest.fixture
def auth_method(storage_config: StorageConfig):
    return storage_config.details[StorageDetails.AUTH_METHOD.value]


@pytest.fixture
def file_key():
    return "test-file.pdf"


class TestS3ClientInitialization:
    """Tests for S3 client initialization and error handling."""

    @pytest.mark.parametrize(
        "mock_get_s3_client, expected_exception, expected_message",
        [
            param(
                lambda auth_method, storage_secrets: "mock_s3_client",
                None,
                None,
                id="success",
            ),
            param(
                lambda auth_method, storage_secrets: (
                    _ for _ in ()  # Empty generator to raise exception
                ).throw(
                    ClientError(
                        {"Error": {"Code": "403", "Message": "Access Denied"}},
                        "GetObject",
                    )
                ),
                ClientError,
                "Access Denied",
                id="client_error",
            ),
            param(
                lambda auth_method, storage_secrets: (
                    _ for _ in ()  # Empty generator to raise exception
                ).throw(ParamValidationError(report="Invalid parameters")),
                ValueError,
                "The parameters you provided are incorrect",
                id="param_validation_error",
            ),
        ],
    )
    def test_maybe_get_s3_client(
        self, monkeypatch, mock_get_s3_client, expected_exception, expected_message
    ):
        """Test S3 client initialization for various scenarios:
        - Successful client creation
        - ClientError handling
        - Parameter validation error handling
        """
        monkeypatch.setattr(
            "fides.api.service.storage.s3.get_s3_client", mock_get_s3_client
        )

        auth_method = "test_auth_method"
        storage_secrets = {"key": "value"}

        if expected_exception:
            with pytest.raises(expected_exception) as excinfo:
                maybe_get_s3_client(auth_method, storage_secrets)
            assert expected_message in str(excinfo.value)
        else:
            result = maybe_get_s3_client(auth_method, storage_secrets)
            assert result == "mock_s3_client"


class TestS3Upload:
    """Tests for S3 upload functionality."""

    @pytest.mark.parametrize(
        "document",
        [
            BytesIO(TEST_DOCUMENT),
            TEST_SPOOLED_DOC,
        ],
    )
    def test_upload_with_different_file_types(
        self,
        s3_client,
        document,
        storage_config,
        bucket_name,
        file_key,
        auth_method,
        monkeypatch,
    ):
        """Test uploading different types of file objects (BytesIO and SpooledTemporaryFile)."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        if isinstance(document, SpooledTemporaryFile):
            document.write(TEST_DOCUMENT)
            document.seek(0)
            copy_document = document.read()
            document.seek(0)
        else:
            copy_document = document.getvalue()

        file_size, presigned_url = generic_upload_to_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key=file_key,
            auth_method=auth_method,
            document=document,
        )

        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        assert response["Body"].read() == copy_document
        assert bucket_name in presigned_url
        assert file_size == len(copy_document)

    def test_upload_with_invalid_bucket(
        self, s3_client, file_key, auth_method, monkeypatch
    ):
        """Test upload behavior when bucket doesn't exist."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        # Invalid bucket name
        bucket_name = "test-bucket"
        storage_secrets = {
            "aws_access_key_id": "fake_access",
            "aws_secret_access_key": "fake",
            "region_name": "us-east-1",
        }
        document = b"This is a test document."

        with pytest.raises(Exception) as e:
            generic_upload_to_s3(
                storage_secrets=storage_secrets,
                bucket_name=bucket_name,
                file_key=file_key,
                auth_method=auth_method,
                document=document,
            )
            assert "NoSuchBucket" in str(e.value)

    @pytest.mark.parametrize(
        "file_type",
        FILE_TYPES,
    )
    def test_upload_with_different_file_types(
        self,
        file_type,
        s3_client,
        storage_config,
        bucket_name,
        auth_method,
        monkeypatch,
    ):
        """Test uploading different types of file objects (BytesIO and SpooledTemporaryFile)."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        file_key = f"test-file.{file_type}"
        document = BytesIO(TEST_DOCUMENT)
        # Getting the value of the document to compare after upload, to avoid closed file error
        copy_document = document.getvalue()

        if file_type in ALLOWED_FILE_TYPES:
            file_size, presigned_url = generic_upload_to_s3(
                storage_secrets=storage_config.secrets,
                bucket_name=bucket_name,
                file_key=file_key,
                auth_method=auth_method,
                document=document,
            )

            assert file_size == len(copy_document)
            assert bucket_name in presigned_url
        else:
            with pytest.raises(Exception) as e:
                generic_upload_to_s3(
                    storage_secrets=storage_config.secrets,
                    bucket_name=bucket_name,
                    file_key=file_key,
                    auth_method=auth_method,
                    document=document,
                )
                assert "Invalid file type" in str(e.value)


class TestS3Retrieve:
    """Tests for S3 file retrieval functionality."""

    def test_retrieve_small_file(
        self, s3_client, storage_config, file_key, auth_method, bucket_name, monkeypatch
    ):
        """Test retrieving a small file from S3."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        s3 = s3_client
        document = b"This is a test document."

        s3.put_object(Bucket=bucket_name, Key=file_key, Body=document)

        file_size, download_link = generic_retrieve_from_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key=file_key,
            auth_method=auth_method,
        )

        assert file_size == len(document)
        assert bucket_name in download_link

    def test_retrieve_large_file(
        self, s3_client, storage_config, file_key, auth_method, bucket_name, monkeypatch
    ):
        """Test retrieving a large file from S3."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        s3 = s3_client
        document = b"0" * (LARGE_FILE_THRESHOLD + 1)

        s3.put_object(Bucket=bucket_name, Key=file_key, Body=document)

        file_size, presigned_url = generic_retrieve_from_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key=file_key,
            auth_method=auth_method,
        )

        assert file_size == len(document)
        assert bucket_name in presigned_url

    def test_retrieve_nonexistent_file(
        self, s3_client, storage_config, file_key, auth_method, bucket_name, monkeypatch
    ):
        """Test behavior when trying to retrieve a non-existent file."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        s3 = s3_client

        with pytest.raises(Exception) as e:
            generic_retrieve_from_s3(
                storage_secrets=storage_config.secrets,
                bucket_name=bucket_name,
                file_key=file_key,
                auth_method=auth_method,
            )
            assert "NoSuchKey" in str(e.value)

    @pytest.mark.parametrize(
        "file_type",
        list(ALLOWED_FILE_TYPES.keys()),
    )
    def test_retrieve_file_types(
        self,
        file_type,
        s3_client,
        storage_config,
        file_key,
        auth_method,
        bucket_name,
        monkeypatch,
    ):
        """Test retrieving a file with different file types and verify content type."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        file_key = f"test-file.{file_type}"
        document = BytesIO(TEST_DOCUMENT)
        # Getting the value of the document to compare after upload, to avoid closed file error
        copy_document = document.getvalue()
        expected_content_type = ALLOWED_FILE_TYPES[file_type]
        _, _ = generic_upload_to_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key=file_key,
            auth_method=auth_method,
            document=document,
        )

        file_size, presigned_url = generic_retrieve_from_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key=file_key,
            auth_method=auth_method,
        )

        assert file_size == len(copy_document)
        assert bucket_name in presigned_url
        # Verify the content type is correctly set in the presigned URL
        assert f"response-content-type={file_type}" in presigned_url.lower()


class TestS3Delete:
    """Tests for S3 file deletion functionality."""

    def test_delete_existing_file(
        self, s3_client, storage_config, file_key, auth_method, bucket_name, monkeypatch
    ):
        """Test deleting an existing file from S3."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        s3 = s3_client
        document = b"This is a test document."

        s3_client.put_object(Bucket=bucket_name, Key=file_key, Body=document)

        generic_delete_from_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key=file_key,
            auth_method=auth_method,
        )

        with pytest.raises(Exception) as e:
            s3_client.get_object(Bucket=bucket_name, Key=file_key)
            assert "NoSuchKey" in str(e.value)

    def test_delete_nonexistent_file(
        self, s3_client, storage_config, file_key, auth_method, bucket_name, monkeypatch
    ):
        """Test behavior when trying to delete a non-existent file."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        s3 = s3_client

        with pytest.raises(Exception) as e:
            generic_delete_from_s3(
                storage_secrets=storage_config.secrets,
                bucket_name=bucket_name,
                file_key=file_key,
                auth_method=auth_method,
            )
            assert "NoSuchKey" in str(e.value)
