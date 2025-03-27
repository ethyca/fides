from io import BytesIO
from tempfile import SpooledTemporaryFile

import boto3
import pytest
from botocore.exceptions import ClientError, ParamValidationError
from moto import mock_aws
from pytest import param

from fides.api.schemas.storage.storage import StorageDetails
from fides.api.service.storage.s3 import (
    LARGE_FILE_THRESHOLD,
    LARGE_FILE_WARNING_TEXT,
    generic_delete_from_s3,
    generic_retrieve_from_s3,
    generic_upload_to_s3,
    maybe_get_s3_client,
)

TEST_DOCUMENT = b"This is a test document."
TEST_SPOOLED_DOC = SpooledTemporaryFile()


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
                    {"Error": {"Code": "403", "Message": "Access Denied"}}, "GetObject"
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
    monkeypatch, mock_get_s3_client, expected_exception, expected_message
):
    """
    Test maybe_get_s3_client for all potential outcomes:
    - Successful return of s3_client
    - Raising ClientError
    - Raising ParamValidationError
    """

    # Mock the get_s3_client function
    monkeypatch.setattr(
        "fides.api.service.storage.s3.get_s3_client", mock_get_s3_client
    )

    auth_method = "test_auth_method"
    storage_secrets = {"key": "value"}  # Example secrets

    if expected_exception:
        # Test for exceptions
        with pytest.raises(expected_exception) as excinfo:
            maybe_get_s3_client(auth_method, storage_secrets)
        assert expected_message in str(excinfo.value)
    else:
        result = maybe_get_s3_client(auth_method, storage_secrets)
        assert result == "mock_s3_client"


@pytest.mark.parametrize(
    "document",
    [
        BytesIO(TEST_DOCUMENT),
        TEST_SPOOLED_DOC,
    ],
)
def test_generic_upload_to_s3(s3_client, document, storage_config, monkeypatch):
    """
    Test that generic_upload_to_s3 can handle both BytesIO and SpooledTemporaryFile.
    """

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    # Prepare the document content
    if isinstance(document, SpooledTemporaryFile):
        document.write(TEST_DOCUMENT)
        document.seek(0)  # Reset the file pointer to the beginning
        copy_document = document.read()
        document.seek(0)  # Reset the file pointer for the upload

    else:
        copy_document = document.getvalue()

    bucket_name = storage_config.details[StorageDetails.BUCKET.value]
    storage_secrets = storage_config.secrets
    file_key = "test-file"
    auth_method = storage_config.details[StorageDetails.AUTH_METHOD.value]

    presigned_url = generic_upload_to_s3(
        storage_secrets=storage_secrets,
        bucket_name=bucket_name,
        file_key=file_key,
        auth_method=auth_method,
        document=document,
    )

    # Verify the file was uploaded
    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    assert response["Body"].read() == copy_document

    # Verify the presigned URL is generated
    assert bucket_name in presigned_url


def test_upload_with_invalid_bucket(s3_client, storage_config, monkeypatch):

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    bucket_name = "test-bucket"
    storage_secrets = {
        "aws_access_key_id": "fake_access",
        "aws_secret_access_key": "fake",
        "region_name": "us-east-1",
    }
    file_key = "test-file"
    auth_method = storage_config.details[StorageDetails.AUTH_METHOD.value]
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


def test_generic_download_from_s3_with_large_file(
    s3_client, storage_config, monkeypatch
):

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    bucket_name = storage_config.details[StorageDetails.BUCKET.value]
    storage_secrets = storage_config.secrets
    file_key = "test-file"
    auth_method = storage_config.details[StorageDetails.AUTH_METHOD.value]
    document = BytesIO(b"0" * (LARGE_FILE_THRESHOLD))  # 5 MB document

    copy_document = document.getvalue()

    presigned_url = generic_upload_to_s3(
        storage_secrets=storage_secrets,
        bucket_name=bucket_name,
        file_key=file_key,
        auth_method=auth_method,
        document=document,
    )

    # Verify the file was uploaded
    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    assert response["Body"].read() == copy_document

    # Verify the presigned URL is generated
    assert bucket_name in presigned_url


def test_generic_retrieve_from_s3(s3_client, storage_config, monkeypatch):

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    s3, bucket_name = s3_client, storage_config.details[StorageDetails.BUCKET.value]
    storage_secrets = storage_config.secrets
    file_key = "test-file"
    auth_method = storage_config.details[StorageDetails.AUTH_METHOD.value]
    document = b"This is a test document."

    # Upload the document first
    s3.put_object(Bucket=bucket_name, Key=file_key, Body=document)

    # Retrieve the document
    retrieved_document, download_link = generic_retrieve_from_s3(
        storage_secrets=storage_secrets,
        bucket_name=bucket_name,
        file_key=file_key,
        auth_method=auth_method,
    )

    # Verify the document was retrieved correctly
    assert retrieved_document == document
    assert bucket_name in download_link


def test_generic_retrieve_from_s3_with_large_file(
    s3_client, storage_config, monkeypatch
):

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    s3, bucket_name = s3_client, storage_config.details[StorageDetails.BUCKET.value]
    storage_secrets = storage_config.secrets
    file_key = "test-file"
    auth_method = storage_config.details[StorageDetails.AUTH_METHOD.value]
    document = b"0" * (LARGE_FILE_THRESHOLD + 1)  # 5 MB document

    # Upload the document first
    s3.put_object(Bucket=bucket_name, Key=file_key, Body=document)

    # Retrieve the document
    warning_text, presigned_url = generic_retrieve_from_s3(
        storage_secrets=storage_secrets,
        bucket_name=bucket_name,
        file_key=file_key,
        auth_method=auth_method,
    )

    # Verify the document was retrieved correctly
    assert warning_text == LARGE_FILE_WARNING_TEXT
    assert bucket_name in presigned_url


def test_generic_retrieve_file_not_found(s3_client, storage_config, monkeypatch):

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    bucket_name = storage_config.details[StorageDetails.BUCKET.value]
    storage_secrets = storage_config.secrets
    file_key = "test-file"
    auth_method = storage_config.details[StorageDetails.AUTH_METHOD.value]

    with pytest.raises(Exception) as e:
        generic_retrieve_from_s3(
            storage_secrets=storage_secrets,
            bucket_name=bucket_name,
            file_key=file_key,
            auth_method=auth_method,
        )

        assert "NoSuchKey" in str(e.value)


def test_generic_delete_from_s3(s3_client, storage_config, monkeypatch):
    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    bucket_name = storage_config.details[StorageDetails.BUCKET.value]
    storage_secrets = storage_config.secrets
    file_key = "test-file"
    auth_method = storage_config.details[StorageDetails.AUTH_METHOD.value]
    document = b"This is a test document."

    # Upload the document first
    s3_client.put_object(Bucket=bucket_name, Key=file_key, Body=document)

    # Delete the document
    generic_delete_from_s3(
        storage_secrets=storage_secrets,
        bucket_name=bucket_name,
        file_key=file_key,
        auth_method=auth_method,
    )

    with pytest.raises(Exception) as e:
        s3_client.get_object(Bucket=bucket_name, Key=file_key)

        assert "NoSuchKey" in str(e.value)


def test_generic_delete_file_not_found(s3_client, storage_config, monkeypatch):
    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    bucket_name = storage_config.details[StorageDetails.BUCKET.value]
    storage_secrets = storage_config.secrets
    file_key = "test-file"
    auth_method = storage_config.details[StorageDetails.AUTH_METHOD.value]

    with pytest.raises(Exception) as e:
        generic_delete_from_s3(
            storage_secrets=storage_secrets,
            bucket_name=bucket_name,
            file_key=file_key,
            auth_method=auth_method,
        )

        assert "NoSuchKey" in str(e.value)
