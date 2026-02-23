from typing import Generator
from unittest import mock
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fides.api.models.application_config import ApplicationConfig
from fides.api.models.sql_models import DataCategory as DataCategoryDbModel
from fides.api.models.storage import (
    ResponseFormat,
    StorageConfig,
    _create_local_default_storage,
    default_storage_config_name,
)
from fides.api.schemas.storage.storage import (
    AWSAuthMethod,
    FileNaming,
    GCSAuthMethod,
    StorageDetails,
    StorageSecrets,
    StorageType,
)


@pytest.fixture(scope="session", autouse=True)
def mock_upload_logic() -> Generator:
    with mock.patch(
        "fides.service.storage.storage_uploader_service.upload_to_s3"
    ) as _fixture:
        _fixture.return_value = "http://www.data-download-url"
        yield _fixture


@pytest.fixture(scope="function")
def custom_data_category(db: Session) -> Generator:
    category = DataCategoryDbModel.create(
        db=db,
        data={
            "name": "Example Custom Data Category",
            "description": "A custom data category for testing",
            "fides_key": "test_custom_data_category",
        },
    )
    yield category
    category.delete(db)


@pytest.fixture(scope="function")
def storage_config(db: Session) -> Generator:
    name = str(uuid4())
    data = {
        "name": name,
        "type": StorageType.s3,
        "details": {
            StorageDetails.AUTH_METHOD.value: AWSAuthMethod.SECRET_KEYS.value,
            StorageDetails.NAMING.value: FileNaming.request_id.value,
            StorageDetails.BUCKET.value: "test_bucket",
        },
        "key": "my_test_config",
        "format": ResponseFormat.json,
    }

    storage_config = StorageConfig.get_by_key_or_id(db, data=data)
    if storage_config is None:
        storage_config = StorageConfig.create(
            db=db,
            data=data,
        )
    storage_config.set_secrets(
        db=db,
        storage_secrets={
            StorageSecrets.AWS_ACCESS_KEY_ID.value: "1234",
            StorageSecrets.AWS_SECRET_ACCESS_KEY.value: "5678",
        },
    )
    yield storage_config
    storage_config.delete(db)


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
def storage_config_default(db: Session) -> Generator:
    """
    Create and yield a default storage config, as defined by its
    `is_default` flag being set to `True`. This is an s3 storage config.
    """
    sc = StorageConfig.create(
        db=db,
        data={
            "name": default_storage_config_name(StorageType.s3.value),
            "type": StorageType.s3,
            "is_default": True,
            "details": {
                StorageDetails.NAMING.value: FileNaming.request_id.value,
                StorageDetails.AUTH_METHOD.value: AWSAuthMethod.AUTOMATIC.value,
                StorageDetails.BUCKET.value: "test_bucket",
            },
            "format": ResponseFormat.json,
        },
    )
    yield sc


@pytest.fixture(scope="function")
def storage_config_default_s3_secret_keys(db: Session) -> Generator:
    """
    Create and yield a default storage config, as defined by its
    `is_default` flag being set to `True`. This is an s3 storage config.
    """
    sc = StorageConfig.create(
        db=db,
        data={
            "name": default_storage_config_name(StorageType.s3.value),
            "type": StorageType.s3,
            "is_default": True,
            "details": {
                StorageDetails.NAMING.value: FileNaming.request_id.value,
                StorageDetails.AUTH_METHOD.value: AWSAuthMethod.SECRET_KEYS.value,
                StorageDetails.BUCKET.value: "test_bucket",
            },
            "secrets": {
                StorageSecrets.AWS_ACCESS_KEY_ID.value: "access_key_id",
                StorageSecrets.AWS_SECRET_ACCESS_KEY.value: "secret_access_key",
            },
            "format": ResponseFormat.json,
        },
    )
    yield sc


@pytest.fixture(scope="function")
def storage_config_default_gcs(db: Session) -> Generator:
    """
    Create and yield a default storage config, as defined by its
    `is_default` flag being set to `True`. This is a Google Cloud Storage config.
    """
    sc = StorageConfig.create(
        db=db,
        data={
            "name": default_storage_config_name(StorageType.gcs.value),
            "type": StorageType.gcs,
            "is_default": True,
            "details": {
                StorageDetails.NAMING.value: FileNaming.request_id.value,
                StorageDetails.AUTH_METHOD.value: GCSAuthMethod.ADC.value,
                StorageDetails.BUCKET.value: "test_bucket",
            },
            "format": ResponseFormat.json,
        },
    )
    yield sc


@pytest.fixture(scope="function")
def storage_config_default_gcs_service_account_keys(db: Session) -> Generator:
    """
    Create and yield a default storage config, as defined by its
    `is_default` flag being set to `True`. This is a Google Cloud Storage config.
    """
    sc = StorageConfig.create(
        db=db,
        data={
            "name": default_storage_config_name(StorageType.gcs.value),
            "type": StorageType.gcs,
            "is_default": True,
            "details": {
                StorageDetails.NAMING.value: FileNaming.request_id.value,
                StorageDetails.AUTH_METHOD.value: GCSAuthMethod.SERVICE_ACCOUNT_KEYS.value,
                StorageDetails.BUCKET.value: "test_bucket",
            },
            "secrets": {
                "type": "service_account",
                "project_id": "test-project-123",
                "private_key_id": "test-key-id-456",
                "private_key": (
                    "-----BEGIN PRIVATE KEY-----\nMIItest\n-----END PRIVATE KEY-----\n"
                ),
                "client_email": "test-service@test-project-123.iam.gserviceaccount.com",
                "client_id": "123456789",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": (
                    "https://www.googleapis.com/oauth2/v1/certs"
                ),
                "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test-service%40test-project-123.iam.gserviceaccount.com",
                "universe_domain": "googleapis.com",
            },
            "format": ResponseFormat.json,
        },
    )
    yield sc


@pytest.fixture(scope="function")
def storage_config_default_local(db: Session) -> Generator:
    """
    Create and yield the default local storage config.
    """
    sc = _create_local_default_storage(db)
    yield sc


@pytest.fixture(scope="function")
def set_active_storage_s3(db) -> None:
    ApplicationConfig.create_or_update(
        db,
        data={
            "api_set": {
                "storage": {"active_default_storage_type": StorageType.s3.value}
            }
        },
    )
