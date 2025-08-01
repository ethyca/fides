from io import BytesIO
from tempfile import SpooledTemporaryFile

import boto3
import pytest
import requests
from botocore.exceptions import ClientError, ParamValidationError
from loguru import logger
from pytest import param

from fides.api.models.storage import StorageConfig
from fides.api.schemas.storage.storage import (
    AWSAuthMethod,
    StorageDetails,
    StorageSecrets,
)
from fides.api.service.storage.s3 import (
    create_presigned_url_for_s3,
    generic_delete_from_s3,
    generic_retrieve_from_s3,
    generic_upload_to_s3,
    get_file_size,
    maybe_get_s3_client,
)
from fides.api.service.storage.util import LARGE_FILE_THRESHOLD, AllowedFileType
from fides.api.util.aws_util import get_s3_client

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


ALLOWED_FILE_TYPES = [ft.name for ft in AllowedFileType]


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
    def test_upload_with_spooled_and_bytes_types(
        self,
        s3_client,
        document,
        storage_config,
        bucket_name,
        file_key,
        auth_method,
        monkeypatch,
    ):
        """Test uploading BytesIO and SpooledTemporaryFile types."""

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

        # Verify file exists
        file_obj = BytesIO()
        s3_client.download_fileobj(Bucket=bucket_name, Key=file_key, Fileobj=file_obj)
        file_obj.seek(0)
        assert file_obj.read() == copy_document
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

        # Verify file doesn't exist using head_object
        with pytest.raises(ClientError) as e:
            s3_client.head_object(Bucket=bucket_name, Key=file_key)

    @pytest.mark.parametrize(
        "file_type",
        ALLOWED_FILE_TYPES,
    )
    def test_upload_with_allowed_file_types(
        self,
        file_type,
        s3_client,
        storage_config,
        bucket_name,
        auth_method,
        monkeypatch,
    ):
        """Test uploading allowed file types."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        file_key = f"test-file.{file_type}"
        document = BytesIO(TEST_DOCUMENT)
        # Getting the value of the document to compare after upload, to avoid closed file error
        copy_document = document.getvalue()

        file_size, presigned_url = generic_upload_to_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key=file_key,
            auth_method=auth_method,
            document=document,
        )

        # Verify file exists
        file_obj = BytesIO()
        s3_client.download_fileobj(Bucket=bucket_name, Key=file_key, Fileobj=file_obj)
        file_obj.seek(0)
        assert file_obj.read() == copy_document
        assert file_size == len(copy_document)
        assert bucket_name in presigned_url

    @pytest.mark.parametrize(
        "file_type",
        NON_ALLOWED_FILE_TYPES,
    )
    def test_upload_with_disallowed_file_types(
        self,
        file_type,
        s3_client,
        storage_config,
        bucket_name,
        auth_method,
        monkeypatch,
    ):
        """Test uploading disallowed file types."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        file_key = f"test-file.{file_type}"
        document = BytesIO(TEST_DOCUMENT)

        with pytest.raises(Exception) as e:
            generic_upload_to_s3(
                storage_secrets=storage_config.secrets,
                bucket_name=bucket_name,
                file_key=file_key,
                auth_method=auth_method,
                document=document,
            )
        assert "Invalid or unallowed file extension" in str(e.value)

    def test_upload_with_custom_size_threshold(
        self, s3_client, storage_config, bucket_name, file_key, auth_method, monkeypatch
    ):
        """Test uploading with a custom size threshold."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        document = BytesIO(b"0" * 1000)  # 1KB file
        custom_threshold = 500  # 500 bytes threshold

        file_size, presigned_url = generic_upload_to_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key=file_key,
            auth_method=auth_method,
            document=document,
            size_threshold=custom_threshold,
        )

        # Verify file exists
        file_obj = BytesIO()
        s3_client.download_fileobj(Bucket=bucket_name, Key=file_key, Fileobj=file_obj)
        file_obj.seek(0)
        assert file_obj.read() == document.getvalue()
        assert file_size == len(document.getvalue())
        assert bucket_name in presigned_url

    def test_upload_with_invalid_file_pointer(
        self, s3_client, storage_config, bucket_name, file_key, auth_method, monkeypatch
    ):
        """Test uploading with an invalid file pointer."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        class InvalidFile:
            def read(self):
                return b"test"

            # Missing seek method

        document = InvalidFile()

        with pytest.raises(TypeError) as e:
            generic_upload_to_s3(
                storage_secrets=storage_config.secrets,
                bucket_name=bucket_name,
                file_key=file_key,
                auth_method=auth_method,
                document=document,
            )
        assert "must be a file-like object supporting 'read' and 'seek'" in str(e.value)


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

    def test_retrieve_small_file_with_ttl(
        self, s3_client, storage_config, file_key, auth_method, bucket_name, monkeypatch
    ):
        """Test retrieving a small file from S3 with custom TTL."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        s3 = s3_client
        document = b"This is a test document."

        s3.put_object(Bucket=bucket_name, Key=file_key, Body=document)

        ttl_seconds = 3600  # 1 hour
        file_size, download_link = generic_retrieve_from_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key=file_key,
            auth_method=auth_method,
            ttl_seconds=ttl_seconds,
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
        ALLOWED_FILE_TYPES,
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
        _, _ = generic_upload_to_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key=file_key,
            auth_method=auth_method,
            document=document,
        )

        # Verify the content type was set correctly during upload
        head_response = s3_client.head_object(Bucket=bucket_name, Key=file_key)
        assert head_response["ContentType"] == AllowedFileType[file_type].value

        file_size, presigned_url = generic_retrieve_from_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key=file_key,
            auth_method=auth_method,
        )

        # Verify file exists
        file_obj = BytesIO()
        s3_client.download_fileobj(Bucket=bucket_name, Key=file_key, Fileobj=file_obj)
        file_obj.seek(0)
        assert file_obj.read() == copy_document
        assert file_size == len(copy_document)
        assert bucket_name in presigned_url

    def test_retrieve_with_content(
        self, s3_client, storage_config, file_key, auth_method, bucket_name, monkeypatch
    ):
        """Test retrieving file content directly from S3 with get_content=True."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        s3 = s3_client
        document = b"This is a test document."

        s3.put_object(Bucket=bucket_name, Key=file_key, Body=document)

        file_size, content = generic_retrieve_from_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key=file_key,
            auth_method=auth_method,
            get_content=True,
        )

        assert file_size == len(document)
        assert content.read() == document

    def test_retrieve_large_file_with_content(
        self, s3_client, storage_config, file_key, auth_method, bucket_name, monkeypatch
    ):
        """Test retrieving a large file's content directly from S3."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        s3 = s3_client
        document = b"0" * (LARGE_FILE_THRESHOLD + 1)

        s3.put_object(Bucket=bucket_name, Key=file_key, Body=document)

        file_size, content = generic_retrieve_from_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key=file_key,
            auth_method=auth_method,
            get_content=True,
        )

        assert file_size == len(document)
        # content is a presigned URL
        assert isinstance(content, str)

    def test_retrieve_nonexistent_file_with_content(
        self, s3_client, storage_config, file_key, auth_method, bucket_name, monkeypatch
    ):
        """Test behavior when trying to retrieve content of a non-existent file."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        with pytest.raises(Exception) as e:
            generic_retrieve_from_s3(
                storage_secrets=storage_config.secrets,
                bucket_name=bucket_name,
                file_key=file_key,
                auth_method=auth_method,
                get_content=True,
            )
        assert "Not Found" in str(e.value)


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

    def test_delete_folder(
        self, s3_client, storage_config, auth_method, bucket_name, monkeypatch
    ):
        """Test deleting a folder (all objects with a prefix)."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        s3 = s3_client
        folder_prefix = "test-folder/"
        files = [
            f"{folder_prefix}file1.txt",
            f"{folder_prefix}file2.txt",
            f"{folder_prefix}subfolder/file3.txt",
        ]

        # Upload multiple files
        for file_key in files:
            s3.put_object(Bucket=bucket_name, Key=file_key, Body=b"test content")

        # Delete the folder
        generic_delete_from_s3(
            storage_secrets=storage_config.secrets,
            bucket_name=bucket_name,
            file_key=folder_prefix,
            auth_method=auth_method,
        )

        # Verify all files are deleted
        for file_key in files:
            with pytest.raises(Exception) as e:
                s3.get_object(Bucket=bucket_name, Key=file_key)
            assert "NoSuchKey" in str(e.value)


class TestS3PresignedUrlAndFileSize:
    """Tests for S3 presigned URL generation and file size retrieval functionality."""

    def test_create_presigned_url(
        self, s3_client, storage_config, file_key, auth_method, bucket_name, monkeypatch
    ):
        """Test creating a presigned URL for an S3 object."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        s3 = s3_client
        document = b"This is a test document."

        # Upload a test file
        s3.put_object(Bucket=bucket_name, Key=file_key, Body=document)

        # Create presigned URL
        presigned_url = create_presigned_url_for_s3(s3_client, bucket_name, file_key)

        # Verify the presigned URL contains the bucket and file key
        assert bucket_name in presigned_url
        assert file_key in presigned_url
        assert presigned_url.startswith("https://")

    def test_create_presigned_url_with_ttl(
        self, s3_client, storage_config, file_key, auth_method, bucket_name, monkeypatch
    ):
        """Test creating a presigned URL for an S3 object with custom TTL."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        s3 = s3_client
        document = b"This is a test document."

        # Upload a test file
        s3.put_object(Bucket=bucket_name, Key=file_key, Body=document)

        # Create presigned URL with custom TTL
        ttl_seconds = 3600  # 1 hour
        presigned_url = create_presigned_url_for_s3(
            s3_client, bucket_name, file_key, ttl_seconds
        )

        # Verify the presigned URL contains the bucket and file key
        assert bucket_name in presigned_url
        assert file_key in presigned_url
        assert presigned_url.startswith("https://")

    def test_create_presigned_url_with_invalid_ttl(
        self, s3_client, storage_config, file_key, auth_method, bucket_name, monkeypatch
    ):
        """Test creating a presigned URL with invalid TTL."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        s3 = s3_client
        document = b"This is a test document."

        # Upload a test file
        s3.put_object(Bucket=bucket_name, Key=file_key, Body=document)

        # Try to create presigned URL with invalid TTL
        invalid_ttl = 604801  # More than 7 days
        with pytest.raises(ValueError) as e:
            create_presigned_url_for_s3(s3_client, bucket_name, file_key, invalid_ttl)
        assert "TTL must be less than 7 days" in str(e.value)

    def test_get_file_size(
        self, s3_client, storage_config, file_key, auth_method, bucket_name, monkeypatch
    ):
        """Test retrieving file size from S3."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        s3 = s3_client
        document = b"This is a test document."
        expected_size = len(document)

        # Upload a test file
        s3.put_object(Bucket=bucket_name, Key=file_key, Body=document)

        # Get file size
        file_size = get_file_size(s3_client, bucket_name, file_key)

        # Verify the file size
        assert file_size == expected_size

    def test_get_file_size_nonexistent_file(
        self, s3_client, storage_config, file_key, auth_method, bucket_name, monkeypatch
    ):
        """Test behavior when trying to get size of a non-existent file."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        s3 = s3_client

        with pytest.raises(Exception) as e:
            get_file_size(s3_client, bucket_name, file_key)
            assert "NoSuchKey" in str(e.value)


@pytest.mark.integration_external
def test_s3_signature_version_4(
    aws_credentials, kms_encrypted_s3_bucket, test_object_key
):
    """
    Test that signature version 4 is required for KMS-encrypted S3 objects.

    Validates that:
    1. Presigned URLs fail without signature version 4
    2. Presigned URLs work with signature version 4 (our s3_client)
    """
    test_content = b"Test content for KMS signature version validation"

    # Upload test object
    standard_client = boto3.client(
        "s3",
        aws_access_key_id=aws_credentials["aws_access_key_id"],
        aws_secret_access_key=aws_credentials["aws_secret_access_key"],
        region_name=aws_credentials["region"],
    )

    standard_client.put_object(
        Bucket=kms_encrypted_s3_bucket,
        Key=test_object_key,
        Body=test_content,
        ServerSideEncryption="aws:kms",
    )

    # Test 1: Generate presigned URL without signature version 4 (should fail)
    client_without_v4 = boto3.client(
        "s3",
        aws_access_key_id=aws_credentials["aws_access_key_id"],
        aws_secret_access_key=aws_credentials["aws_secret_access_key"],
        region_name=aws_credentials["region"],
    )

    old_presigned_url = client_without_v4.generate_presigned_url(
        "get_object",
        Params={"Bucket": kms_encrypted_s3_bucket, "Key": test_object_key},
        ExpiresIn=3600,
    )

    # Verify old URL fails
    response = requests.get(old_presigned_url, timeout=10)
    assert (
        response.status_code != 200
    ), "URL without signature v4 should fail for KMS objects"
    assert (
        "require AWS Signature Version 4" in response.text
        or response.status_code == 400
    )

    # Test 2: Use our S3 client with signature version 4
    storage_secrets = {
        StorageSecrets.AWS_ACCESS_KEY_ID.value: aws_credentials["aws_access_key_id"],
        StorageSecrets.AWS_SECRET_ACCESS_KEY.value: aws_credentials[
            "aws_secret_access_key"
        ],
        "region_name": aws_credentials["region"],
    }

    s3_client = get_s3_client(
        auth_method=AWSAuthMethod.SECRET_KEYS.value, storage_secrets=storage_secrets
    )

    # Verify client uses signature version 4
    assert s3_client.meta.config.signature_version == "s3v4"

    # Generate presigned URL with v4 (should work)
    fixed_presigned_url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": kms_encrypted_s3_bucket, "Key": test_object_key},
        ExpiresIn=3600,
    )

    # Verify v4 URL works
    response = requests.get(fixed_presigned_url, timeout=10)
    assert (
        response.status_code == 200
    ), "URL with signature v4 must work for KMS objects"
    assert response.content == test_content


@pytest.mark.integration_external
def test_s3_signature_version_4_non_kms(
    aws_credentials, regular_s3_bucket, test_object_key
):
    """
    Test that signature version 4 works correctly with non-KMS S3 buckets.

    Validates that:
    1. Presigned URLs work with signature version 4 on regular buckets
    2. Our s3_client maintains backward compatibility with non-KMS buckets
    """
    test_content = b"Test content for non-KMS signature version validation"

    # Upload test object without KMS encryption
    standard_client = boto3.client(
        "s3",
        aws_access_key_id=aws_credentials["aws_access_key_id"],
        aws_secret_access_key=aws_credentials["aws_secret_access_key"],
        region_name=aws_credentials["region"],
    )

    standard_client.put_object(
        Bucket=regular_s3_bucket,
        Key=test_object_key,
        Body=test_content,
    )

    # Test using our S3 client with signature version 4
    storage_secrets = {
        StorageSecrets.AWS_ACCESS_KEY_ID.value: aws_credentials["aws_access_key_id"],
        StorageSecrets.AWS_SECRET_ACCESS_KEY.value: aws_credentials[
            "aws_secret_access_key"
        ],
        "region_name": aws_credentials["region"],
    }

    s3_client = get_s3_client(
        auth_method=AWSAuthMethod.SECRET_KEYS.value, storage_secrets=storage_secrets
    )

    # Verify client uses signature version 4
    assert s3_client.meta.config.signature_version == "s3v4"

    # Generate presigned URL with v4 for non-KMS bucket (should work)
    presigned_url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": regular_s3_bucket, "Key": test_object_key},
        ExpiresIn=3600,
    )

    # Verify URL works for non-KMS bucket
    response = requests.get(presigned_url, timeout=10)
    assert (
        response.status_code == 200
    ), "URL with signature v4 must work for non-KMS objects"
    assert response.content == test_content

    # Test that signature v4 maintains compatibility by also testing
    # with standard client (which defaults to different signature version)
    standard_presigned_url = standard_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": regular_s3_bucket, "Key": test_object_key},
        ExpiresIn=3600,
    )

    # Verify both URLs work for non-KMS bucket
    response_standard = requests.get(standard_presigned_url, timeout=10)
    assert (
        response_standard.status_code == 200
    ), "Standard client URL should work for non-KMS objects"
    assert response_standard.content == test_content
