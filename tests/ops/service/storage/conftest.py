import os
from typing import Generator
from uuid import uuid4

import boto3
import pytest
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.storage import ResponseFormat, StorageConfig
from fides.api.schemas.storage.storage import FileNaming, StorageDetails, StorageType


@pytest.fixture(scope="function")
def storage_config_local(db: Session) -> Generator:
    name = str(uuid4())
    data = {
        "name": name,
        "type": StorageType.local,
        "details": {
            StorageDetails.NAMING.value: FileNaming.request_id.value,
        },
        "key": "my_test_config_local",
        "format": ResponseFormat.json,
    }
    storage_config = StorageConfig.get_by_key_or_id(db, data=data)
    if storage_config is None:
        storage_config = StorageConfig.create(
            db=db,
            data=data,
        )
    yield storage_config
    storage_config.delete(db)


@pytest.fixture(scope="function")
def aws_credentials():
    """Fixture that provides AWS credentials from environment variables."""
    aws_access_key_id = os.environ.get("S3_AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.environ.get("S3_AWS_SECRET_ACCESS_KEY")
    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

    if not aws_access_key_id or not aws_secret_access_key:
        pytest.fail("Real AWS credentials required for KMS integration test")

    return {
        "aws_access_key_id": aws_access_key_id,
        "aws_secret_access_key": aws_secret_access_key,
        "region": region,
    }


@pytest.fixture(scope="function")
def kms_encrypted_s3_bucket(aws_credentials):
    """Fixture that creates a temporary S3 bucket with KMS encryption enabled."""
    bucket_name = f"fides-test-kms-{uuid4()}"

    # Create S3 client for bucket management
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=aws_credentials["aws_access_key_id"],
        aws_secret_access_key=aws_credentials["aws_secret_access_key"],
        region_name=aws_credentials["region"],
    )

    try:
        # Create bucket
        s3_client.create_bucket(Bucket=bucket_name)

        # Enable default KMS encryption on the bucket
        s3_client.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                "Rules": [
                    {"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "aws:kms"}}
                ]
            },
        )

        yield bucket_name

    finally:
        # Cleanup: Delete all objects first, then the bucket
        try:
            # List and delete all objects
            objects = s3_client.list_objects_v2(Bucket=bucket_name)
            if "Contents" in objects:
                for obj in objects["Contents"]:
                    s3_client.delete_object(Bucket=bucket_name, Key=obj["Key"])

            # Delete the bucket
            s3_client.delete_bucket(Bucket=bucket_name)
        except Exception as cleanup_error:
            logger.warning(
                f"Warning: Failed to clean up bucket {bucket_name}: {cleanup_error}"
            )


@pytest.fixture(scope="function")
def test_object_key():
    """Fixture that provides a unique test object key."""
    return f"test-kms-signature-version-{uuid4()}.txt"
