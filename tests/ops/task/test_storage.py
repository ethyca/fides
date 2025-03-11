import boto3
import pytest
from moto import mock_aws

from fides.api.schemas.storage.storage import StorageDetails
from fides.api.tasks.storage import (
    generic_delete_from_s3,
    generic_retrieve_from_s3,
    generic_upload_to_s3,
)


@pytest.fixture
def s3_client(storage_config):
    with mock_aws():
        session = boto3.Session(
            aws_access_key_id="fake_access_key",
            aws_secret_access_key="fake_secret_key",
            region_name="us-east-1",
        )
        s3 = session.client("s3")
        s3.create_bucket(Bucket=storage_config.details[StorageDetails.BUCKET.value])
        yield s3


def test_generic_upload_to_s3(s3_client, storage_config, monkeypatch):

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    bucket_name = storage_config.details[StorageDetails.BUCKET.value]
    storage_secrets = storage_config.secrets
    file_key = "test-file"
    auth_method = storage_config.details[StorageDetails.AUTH_METHOD.value]
    document = b"This is a test document."

    presigned_url = generic_upload_to_s3(
        storage_secrets=storage_secrets,
        bucket_name=bucket_name,
        file_key=file_key,
        auth_method=auth_method,
        document=document,
    )

    # Verify the file was uploaded
    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    assert response["Body"].read() == document

    # Verify the presigned URL is generated
    print(presigned_url)
    assert bucket_name in presigned_url


def test_upload_with_invalid_bucket(s3_client, storage_config, monkeypatch):

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    s3, bucket_name = s3_client, "test-bucket"
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
    retrieved_document = generic_retrieve_from_s3(
        storage_secrets=storage_secrets,
        bucket_name=bucket_name,
        file_key=file_key,
        auth_method=auth_method,
    )

    # Verify the document was retrieved correctly
    assert retrieved_document == document


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
