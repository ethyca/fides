import json
from typing import Dict
from unittest import mock
from unittest.mock import Mock

import pytest
from fastapi_pagination import Params
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fides.api.common_exceptions import KeyOrNameAlreadyExists, KeyValidationError
from fides.api.models.application_config import ApplicationConfig
from fides.api.models.client import ClientDetail
from fides.api.models.storage import StorageConfig, default_storage_config_name
from fides.api.schemas.storage.data_upload_location_response import DataUpload
from fides.api.schemas.storage.storage import (
    AWSAuthMethod,
    FileNaming,
    ResponseFormat,
    StorageConfigStatus,
    StorageConfigStatusMessage,
    StorageDetails,
    StorageSecrets,
    StorageType,
)
from fides.common.api.scope_registry import (
    STORAGE_CREATE_OR_UPDATE,
    STORAGE_DELETE,
    STORAGE_READ,
)
from fides.common.api.v1.urn_registry import (
    STORAGE_ACTIVE_DEFAULT,
    STORAGE_BY_KEY,
    STORAGE_CONFIG,
    STORAGE_DEFAULT,
    STORAGE_DEFAULT_BY_TYPE,
    STORAGE_DEFAULT_SECRETS,
    STORAGE_SECRETS,
    STORAGE_STATUS,
    STORAGE_UPLOAD,
    V1_URL_PREFIX,
)
from fides.config import get_config
from fides.config.config_proxy import ConfigProxy

PAGE_SIZE = Params().size
CONFIG = get_config()


class TestUploadData:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, privacy_request) -> str:
        return (V1_URL_PREFIX + STORAGE_UPLOAD).format(request_id=privacy_request.id)

    @pytest.fixture(scope="function")
    def payload(self, oauth_client: ClientDetail, privacy_request) -> Dict:
        return {
            "storage_key": "s3_destination_key",
            "data": {
                "email": "email@gmail.com",
                "address": "123 main ST, Asheville NC",
                "zip codes": [12345, 54321],
            },
        }

    def test_upload_data_not_authenticated(self, url, api_client: TestClient, payload):
        response = api_client.post(url, headers={}, json=payload)
        assert 401 == response.status_code

    def test_upload_data_wrong_scope(
        self, url, api_client: TestClient, payload, generate_auth_header
    ):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.post(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_invalid_privacy_request(
        self, api_client: TestClient, payload, generate_auth_header
    ):
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        url = (V1_URL_PREFIX + STORAGE_UPLOAD).format(request_id="invalid-id")
        response = api_client.post(url, headers=auth_header, json=payload)
        assert 404 == response.status_code

    @mock.patch("fides.api.api.v1.endpoints.storage_endpoints.upload")
    def test_post_upload_data(
        self,
        mock_post_upload_data: Mock,
        api_client: TestClient,
        generate_auth_header,
        url,
        privacy_request,
        payload,
    ) -> None:
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        expected_location = f"https://bucket.s3.amazonaws.com/{privacy_request.id}.json"
        mock_post_upload_data.return_value = expected_location

        response = api_client.post(url, headers=auth_header, json=payload)
        response_body = json.loads(response.text)

        assert 201 == response.status_code
        mock_post_upload_data.assert_called_with(
            mock.ANY,
            privacy_request=mock.ANY,
            data=payload.get("data"),
            storage_key=payload.get("storage_key"),
        )
        call_kwargs = mock_post_upload_data.call_args.kwargs
        assert call_kwargs["privacy_request"].id == privacy_request.id
        assert response_body == DataUpload(location=expected_location).model_dump(
            mode="json"
        )


class TestPatchStorageConfig:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail) -> str:
        return V1_URL_PREFIX + STORAGE_CONFIG

    @pytest.fixture(scope="function")
    def payload(self):
        return [
            {
                "name": "test destination",
                "type": StorageType.s3.value,
                "details": {
                    "auth_method": AWSAuthMethod.SECRET_KEYS.value,
                    "bucket": "some-bucket",
                    "naming": "some-filename-convention-enum",
                    "max_retries": 10,
                },
                "format": "csv",
            }
        ]

    def test_patch_storage_config_not_authenticated(
        self,
        api_client: TestClient,
        payload,
        url,
    ):
        response = api_client.patch(url, headers={}, json=payload)
        assert 401 == response.status_code

    def test_patch_storage_config_incorrect_scope(
        self,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_patch_storage_config_with_no_key(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.patch(url, headers=auth_header, json=payload)

        assert 200 == response.status_code
        response_body = json.loads(response.text)

        assert response_body["succeeded"][0]["key"] == "test_destination"
        storage_config = db.query(StorageConfig).filter_by(key="test_destination")[0]
        storage_config.delete(db)

    def test_put_storage_config_with_invalid_key(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        payload[0]["key"] = "*invalid-key"
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "Value error, FidesKeys must only contain alphanumeric characters, '.', '_', '<', '>' or '-'. Value provided: *invalid-key"
        )

    def test_patch_storage_config_with_key(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        payload[0]["key"] = "my_s3_bucket"
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])

        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        response_body = json.loads(response.text)
        storage_config = db.query(StorageConfig).filter_by(key="my_s3_bucket")[0]

        expected_response = {
            "succeeded": [
                {
                    "name": "test destination",
                    "type": StorageType.s3.value,
                    "details": {
                        "auth_method": AWSAuthMethod.SECRET_KEYS.value,
                        "bucket": "some-bucket",
                        "naming": "some-filename-convention-enum",
                        "max_retries": 10,
                    },
                    "key": "my_s3_bucket",
                    "format": "csv",
                    "is_default": False,
                }
            ],
            "failed": [],
        }
        assert expected_response == response_body
        storage_config.delete(db)

    @pytest.mark.parametrize(
        "auth_method", [AWSAuthMethod.SECRET_KEYS.value, AWSAuthMethod.AUTOMATIC.value]
    )
    def test_patch_storage_config_with_different_auth_methods(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
        auth_method,
    ):
        payload[0]["key"] = "my_s3_bucket"
        payload[0]["details"]["auth_method"] = auth_method
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.patch(url, headers=auth_header, json=payload)

        assert 200 == response.status_code
        response_body = json.loads(response.text)
        storage_config = db.query(StorageConfig).filter_by(key="my_s3_bucket")[0]
        assert auth_method == response_body["succeeded"][0]["details"]["auth_method"]
        storage_config.delete(db)

    def test_patch_config_response_format_not_specified(
        self,
        url,
        db: Session,
        api_client: TestClient,
        generate_auth_header,
    ):
        key = "my_s3_upload"
        payload = [
            {
                "key": key,
                "name": "my-test-dest",
                "type": StorageType.s3.value,
                "details": {
                    "auth_method": AWSAuthMethod.SECRET_KEYS.value,
                    "bucket": "some-bucket",
                    "naming": "some-filename-convention-enum",
                    "max_retries": 10,
                },
            }
        ]
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])

        response = api_client.patch(url, headers=auth_header, json=payload)
        assert response.status_code == 200
        assert (
            json.loads(response.text)["succeeded"][0]["format"]
            == ResponseFormat.json.value
        )

        # Update storage config
        response = api_client.patch(
            V1_URL_PREFIX + STORAGE_CONFIG, headers=auth_header, json=payload
        )
        assert response.status_code == 200
        assert (
            json.loads(response.text)["succeeded"][0]["format"]
            == ResponseFormat.json.value
        )

        storage_config = StorageConfig.get_by(db=db, field="key", value=key)
        storage_config.delete(db)

    def test_patch_storage_config_missing_detail(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.patch(
            url,
            headers=auth_header,
            json=[
                {
                    "key": "my_s3_upload",
                    "name": "my-test-dest",
                    "type": StorageType.s3.value,
                    "details": {
                        # "bucket": "removed-from-payload",
                        "auth_method": AWSAuthMethod.SECRET_KEYS.value,
                        "naming": "request_id",
                        "max_retries": 10,
                    },
                },
            ],
        )
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert "details" in errors[0]["loc"]
        assert errors[0]["msg"] == "Value error, [\"Field required ('bucket',)\"]"


class TestPutStorageConfigSecretsS3:
    @pytest.fixture(scope="function")
    def url(self, storage_config) -> str:
        return (V1_URL_PREFIX + STORAGE_SECRETS).format(config_key=storage_config.key)

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            StorageSecrets.AWS_ACCESS_KEY_ID.value: "1345234524",
            StorageSecrets.AWS_SECRET_ACCESS_KEY.value: "23451345834789",
        }

    def test_put_config_secrets_unauthenticated(
        self, api_client: TestClient, payload, url
    ):
        response = api_client.put(url, headers={}, json=payload)
        assert 401 == response.status_code

    def test_put_config_secrets_wrong_scope(
        self, api_client: TestClient, payload, url, generate_auth_header
    ):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_put_config_secret_invalid_config(
        self, api_client: TestClient, payload, generate_auth_header
    ):
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        url = (V1_URL_PREFIX + STORAGE_SECRETS).format(config_key="invalid_key")
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 404 == response.status_code

    def test_update_with_invalid_secrets_key(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.put(
            url + "?verify=False", headers=auth_header, json={"bad_key": "12345"}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == [
            "Field required ('aws_access_key_id',)",
            "Field required ('aws_secret_access_key',)",
            "Extra inputs are not permitted ('bad_key',)",
        ]

    def test_put_config_secrets_without_verifying(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
        storage_config,
    ):
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.put(
            url + "?verify=False", headers=auth_header, json=payload
        )
        assert 200 == response.status_code

        db.refresh(storage_config)

        assert json.loads(response.text) == {
            "msg": "Secrets updated for StorageConfig with key: my_test_config.",
            "test_status": None,
            "failure_reason": None,
        }
        assert (
            storage_config.secrets[StorageSecrets.AWS_ACCESS_KEY_ID.value]
            == "1345234524"
        )
        assert (
            storage_config.secrets[StorageSecrets.AWS_SECRET_ACCESS_KEY.value]
            == "23451345834789"
        )

    @mock.patch("fides.api.api.v1.endpoints.storage_endpoints.secrets_are_valid")
    def test_put_config_secrets_and_verify(
        self,
        mock_valid: Mock,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
        storage_config,
    ):
        mock_valid.return_value = True
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        db.refresh(storage_config)

        assert json.loads(response.text) == {
            "msg": "Secrets updated for StorageConfig with key: my_test_config.",
            "test_status": "succeeded",
            "failure_reason": None,
        }
        assert (
            storage_config.secrets[StorageSecrets.AWS_ACCESS_KEY_ID.value]
            == "1345234524"
        )
        assert (
            storage_config.secrets[StorageSecrets.AWS_SECRET_ACCESS_KEY.value]
            == "23451345834789"
        )

        mock_valid.reset_mock()
        mock_valid.return_value = False
        response = api_client.put(url, headers=auth_header, json=payload)
        assert json.loads(response.text) == {
            "msg": "Secrets updated for StorageConfig with key: my_test_config.",
            "test_status": "failed",
            "failure_reason": None,
        }

    @mock.patch(
        "fides.api.service.storage.storage_authenticator_service.get_aws_session"
    )
    def test_put_s3_config_secrets_and_verify(
        self,
        get_aws_session_mock: Mock,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code
        get_aws_session_mock.assert_called_once_with(
            AWSAuthMethod.SECRET_KEYS.value,
            {
                "aws_access_key_id": payload["aws_access_key_id"],
                "aws_secret_access_key": payload["aws_secret_access_key"],
            },
        )


class TestGetStorageConfigs:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail) -> str:
        return V1_URL_PREFIX + STORAGE_CONFIG

    def test_get_configs_not_authenticated(self, api_client: TestClient, url) -> None:
        response = api_client.get(url)
        assert 401 == response.status_code

    def test_get_configs_wrong_scope(
        self, api_client: TestClient, url, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header([STORAGE_DELETE])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_get_configs(
        self, db, api_client: TestClient, url, generate_auth_header, storage_config
    ):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(V1_URL_PREFIX + STORAGE_CONFIG, headers=auth_header)
        assert 200 == response.status_code

        expected_response = {
            "items": [
                {
                    "key": "my_test_config",
                    "name": storage_config.name,
                    "type": storage_config.type.value,
                    "details": {
                        "auth_method": AWSAuthMethod.SECRET_KEYS.value,
                        "bucket": "test_bucket",
                        "naming": "request_id",
                    },
                    "format": "json",
                    "is_default": False,
                }
            ],
            "page": 1,
            "pages": 1,
            "size": PAGE_SIZE,
            "total": 1,
        }
        response_body = json.loads(response.text)
        assert expected_response == response_body


class TestGetStorageConfig:
    @pytest.fixture(scope="function")
    def url(self, storage_config) -> str:
        return (V1_URL_PREFIX + STORAGE_BY_KEY).format(config_key=storage_config.key)

    def test_get_config_not_authenticated(self, url, api_client: TestClient):
        response = api_client.get(url)
        assert 401 == response.status_code

    def test_get_config_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header([STORAGE_DELETE])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_get_config_invalid(
        self, api_client: TestClient, generate_auth_header, storage_config
    ):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(
            (V1_URL_PREFIX + STORAGE_BY_KEY).format(config_key="invalid"),
            headers=auth_header,
        )
        assert 404 == response.status_code

    def test_get_config(
        self, url, api_client: TestClient, generate_auth_header, storage_config
    ):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200

        response_body = json.loads(response.text)

        assert response_body == {
            "name": storage_config.name,
            "type": StorageType.s3.value,
            "details": {
                "auth_method": AWSAuthMethod.SECRET_KEYS.value,
                "bucket": "test_bucket",
                "naming": "request_id",
            },
            "key": "my_test_config",
            "format": "json",
            "is_default": False,
        }


class TestDeleteConfig:
    @pytest.fixture(scope="function")
    def url(self, storage_config) -> str:
        return (V1_URL_PREFIX + STORAGE_BY_KEY).format(config_key=storage_config.key)

    def test_delete_config_not_authenticated(self, url, api_client: TestClient):
        response = api_client.delete(url)
        assert 401 == response.status_code

    def test_delete_config_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.delete(url, headers=auth_header)
        assert 403 == response.status_code

    def test_delete_config_invalid(
        self, api_client: TestClient, generate_auth_header, storage_config
    ):
        auth_header = generate_auth_header([STORAGE_DELETE])
        response = api_client.delete(
            (V1_URL_PREFIX + STORAGE_BY_KEY).format(config_key="invalid"),
            headers=auth_header,
        )
        assert 404 == response.status_code

    def test_delete_default_config_rejected(
        self,
        api_client: TestClient,
        generate_auth_header,
        storage_config_default,
    ):
        auth_header = generate_auth_header([STORAGE_DELETE])
        response = api_client.delete(
            (V1_URL_PREFIX + STORAGE_BY_KEY).format(
                config_key=storage_config_default.key
            ),
            headers=auth_header,
        )
        assert 400 == response.status_code
        assert "Default storage configurations cannot be deleted." in response.text

    def test_delete_config(
        self,
        db: Session,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        # Creating new config, so we don't run into issues trying to clean up a deleted fixture
        storage_config = StorageConfig.create(
            db=db,
            data={
                "name": "My S3 Storage",
                "type": StorageType.s3,
                "details": {
                    StorageDetails.NAMING.value: FileNaming.request_id.value,
                    StorageDetails.BUCKET.value: "test_bucket",
                },
                "key": "my_storage_config",
                "format": ResponseFormat.json,
            },
        )
        url = (V1_URL_PREFIX + STORAGE_BY_KEY).format(config_key=storage_config.key)
        auth_header = generate_auth_header([STORAGE_DELETE])
        response = api_client.delete(url, headers=auth_header)
        assert response.status_code == 204

        db.expunge_all()
        config = db.query(StorageConfig).filter_by(key=storage_config.key).first()
        assert config is None


class TestGetDefaultStorageConfigs:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + STORAGE_DEFAULT

    def test_get_default_configs_not_authenticated(
        self, api_client: TestClient, url
    ) -> None:
        response = api_client.get(url)
        assert 401 == response.status_code

    def test_get_default_configs_wrong_scope(
        self, api_client: TestClient, url, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header([STORAGE_DELETE])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_get_default_configs(
        self,
        db,
        api_client: TestClient,
        url,
        generate_auth_header,
        storage_config_default: StorageConfig,
    ):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code

        expected_response = {
            "items": [
                {
                    "name": storage_config_default.name,
                    "type": storage_config_default.type.value,
                    "details": {
                        "auth_method": storage_config_default.details["auth_method"],
                        "naming": storage_config_default.details["naming"],
                        "bucket": "test_bucket",
                    },
                    "key": storage_config_default.key,
                    "format": storage_config_default.format.value,
                    "is_default": True,
                }
            ],
            "page": 1,
            "pages": 1,
            "size": PAGE_SIZE,
            "total": 1,
        }
        response_body = json.loads(response.text)
        assert expected_response == response_body


class TestGetDefaultStorageConfig:
    @pytest.fixture(scope="function")
    def url(self, storage_config_default: StorageConfig) -> str:
        return (V1_URL_PREFIX + STORAGE_DEFAULT_BY_TYPE).format(
            storage_type=storage_config_default.type.value
        )

    def test_get_default_config_not_authenticated(self, url, api_client: TestClient):
        response = api_client.get(url)
        assert 401 == response.status_code

    def test_get_default_config_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header([STORAGE_DELETE])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_get_default_config_invalid(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        storage_config_default: StorageConfig,
    ):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(
            (V1_URL_PREFIX + STORAGE_DEFAULT_BY_TYPE).format(storage_type="invalid"),
            headers=auth_header,
        )
        assert 422 == response.status_code

    def test_get_default_config_not_exist(
        self,
        api_client: TestClient,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(
            (V1_URL_PREFIX + STORAGE_DEFAULT_BY_TYPE).format(
                storage_type=StorageType.s3.value
            ),
            headers=auth_header,
        )
        assert 404 == response.status_code

    def test_get_default_config(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        storage_config_default: StorageConfig,
    ):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200

        response_body = response.json()

        assert response_body == {
            "name": storage_config_default.name,
            "type": storage_config_default.type.value,
            "details": {
                "auth_method": storage_config_default.details["auth_method"],
                "naming": storage_config_default.details["naming"],
                "bucket": "test_bucket",
            },
            "key": storage_config_default.key,
            "format": storage_config_default.format.value,
            "is_default": True,
        }


class TestPutDefaultStorageConfig:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + STORAGE_DEFAULT

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            "type": StorageType.s3.value,
            "details": {
                "auth_method": AWSAuthMethod.SECRET_KEYS.value,
                "bucket": "some-bucket",
                "max_retries": 10,
            },
            "format": "csv",
        }

    def test_put_default_storage_config_not_authenticated(
        self,
        api_client: TestClient,
        payload,
        url,
    ):
        response = api_client.put(url, headers={}, json=payload)
        assert 401 == response.status_code

    def test_put_default_storage_config_incorrect_scope(
        self,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_put_default_storage(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json=payload)

        assert 200 == response.status_code
        response_body = json.loads(response.text)

        assert response_body["key"] is not None
        assert response_body["type"] == payload["type"]
        assert response_body["details"]["bucket"] == payload["details"]["bucket"]
        assert response_body["is_default"] == True
        storage_configs = db.query(StorageConfig).filter_by(is_default=True).all()
        assert len(storage_configs) == 1
        assert storage_configs[0].key == response_body["key"]
        assert storage_configs[0].type.value == payload["type"]
        assert storage_configs[0].details["bucket"] == payload["details"]["bucket"]
        assert storage_configs[0].is_default

        storage_configs[0].delete(db)

    def test_put_storage_config_with_key_rejected(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        payload["key"] = "my_s3_bucket"
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])

        response = api_client.put(url, headers=auth_header, json=payload)
        assert 422 == response.status_code

    def test_put_storage_config_with_name_rejected(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        payload["name"] = "my_s3_bucket"
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])

        response = api_client.put(url, headers=auth_header, json=payload)
        assert 422 == response.status_code

    @pytest.mark.parametrize(
        "auth_method", [AWSAuthMethod.SECRET_KEYS.value, AWSAuthMethod.AUTOMATIC.value]
    )
    def test_put_default_storage_config_with_different_auth_methods(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
        auth_method,
    ):
        payload["details"]["auth_method"] = auth_method
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json=payload)

        assert 200 == response.status_code
        response_body = json.loads(response.text)
        config_key = response_body["key"]
        storage_config = StorageConfig.get_by(db, field="key", value=config_key)
        assert auth_method == response_body["details"]["auth_method"]
        assert auth_method == storage_config.details["auth_method"]
        assert storage_config.is_default
        storage_config.delete(db)

    def test_put_default_storage_config_twice_only_one_record(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])

        # try an initial put, assert it works well
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code
        response_body = json.loads(response.text)
        config_key = response_body["key"]
        storage_configs = (
            db.query(StorageConfig)
            .filter_by(is_default=True, type=payload["type"])
            .all()
        )
        assert len(storage_configs) == 1
        storage_config = storage_configs[0]
        assert storage_config.key == config_key
        assert storage_config.details["bucket"] == payload["details"]["bucket"]

        # try a follow-up put after changing a detail assert it made the update to existing record
        payload["details"]["bucket"] = "a-new-bucket"
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code
        response_body = json.loads(response.text)
        assert config_key == response_body["key"]
        storage_configs = (
            db.query(StorageConfig)
            .filter_by(is_default=True, type=payload["type"])
            .all()
        )
        assert len(storage_configs) == 1
        storage_config = storage_configs[0]
        db.refresh(storage_config)
        assert storage_config.key == config_key
        assert storage_config.details["bucket"] == "a-new-bucket"

        storage_config.delete(db)

    def test_put_default_config_local_rejects_s3_details(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        payload,
    ):
        payload["type"] = StorageType.local.value
        payload["format"] = (
            ResponseFormat.json.value
        )  # change to JSON because that's what local expects
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])

        response = api_client.put(url, headers=auth_header, json=payload)
        assert response.status_code == 422

    def test_put_default_config_local_rejects_csv(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        payload: dict,
    ):
        payload["type"] = StorageType.local.value
        payload.pop(
            "details"
        )  # get rid of details since local doesn't need any details
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])

        response = api_client.put(url, headers=auth_header, json=payload)
        # 422 here is due to csv not being allowed for local storage
        assert response.status_code == 422

    def test_put_default_config_local(
        self,
        db,
        url,
        api_client: TestClient,
        generate_auth_header,
        payload: dict,
    ):
        payload["type"] = StorageType.local.value
        payload["format"] = (
            ResponseFormat.json.value
        )  # change to JSON because that's what local expects
        payload["details"] = {
            "naming": FileNaming.request_id.value
        }  # currently this is the only thing that can be set for local storage
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])

        response = api_client.put(url, headers=auth_header, json=payload)

        assert 200 == response.status_code
        response_body = json.loads(response.text)

        assert response_body["key"] is not None
        assert response_body["type"] == payload["type"]
        assert response_body["details"]["naming"] == payload["details"]["naming"]
        assert response_body["is_default"] == True
        storage_configs = db.query(StorageConfig).filter_by(is_default=True).all()
        assert len(storage_configs) == 1
        assert storage_configs[0].key == response_body["key"]
        assert storage_configs[0].type.value == payload["type"]
        assert storage_configs[0].details["naming"] == payload["details"]["naming"]
        assert storage_configs[0].is_default

    def test_put_default_storage_config_missing_detail(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.put(
            url,
            headers=auth_header,
            json={
                "type": StorageType.s3.value,
                "details": {
                    # "bucket": "removed-from-payload",
                    "auth_method": AWSAuthMethod.SECRET_KEYS.value,
                    "naming": "request_id",
                    "max_retries": 10,
                },
            },
        )
        assert response.status_code == 422
        assert "Field required" in response.text
        assert "bucket" in response.text

    @mock.patch("fides.api.models.storage.StorageConfig.create_or_update")
    def test_put_default_config_key_or_name_exists(
        self,
        mock_create_or_update: Mock,
        api_client: TestClient,
        url,
        generate_auth_header,
        payload,
    ):
        mock_create_or_update.side_effect = KeyOrNameAlreadyExists("Key already exists")
        payload["type"] = StorageType.local.value
        payload["format"] = (
            ResponseFormat.json.value
        )  # change to JSON because that's what local expects
        payload["details"] = {
            "naming": FileNaming.request_id.value
        }  # currently this is the only thing that can be set for local storage
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])

        response = api_client.put(url, headers=auth_header, json=payload)

        assert 400 == response.status_code

    @mock.patch("fides.api.models.storage.StorageConfig.create_or_update")
    def test_put_default_config_key_error(
        self,
        mock_create_or_update: Mock,
        api_client: TestClient,
        url,
        generate_auth_header,
        payload,
        loguru_caplog,
    ):
        mock_create_or_update.side_effect = KeyValidationError()
        payload["type"] = StorageType.local.value
        payload["format"] = (
            ResponseFormat.json.value
        )  # change to JSON because that's what local expects
        payload["details"] = {
            "naming": FileNaming.request_id.value
        }  # currently this is the only thing that can be set for local storage
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])

        response = api_client.put(url, headers=auth_header, json=payload)

        assert 500 == response.status_code
        assert (
            "Create/update failed for default config update for storage type"
            in loguru_caplog.text
        )


class TestPutDefaultStorageConfigSecretsS3:
    @pytest.fixture(scope="function")
    def url(self, storage_config_default) -> str:
        return (V1_URL_PREFIX + STORAGE_DEFAULT_SECRETS).format(
            storage_type=StorageType.s3.value
        )

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            StorageSecrets.AWS_ACCESS_KEY_ID.value: "1345234524",
            StorageSecrets.AWS_SECRET_ACCESS_KEY.value: "23451345834789",
        }

    def test_put_default_config_secrets_unauthenticated(
        self, api_client: TestClient, payload, url
    ):
        response = api_client.put(url, headers={}, json=payload)
        assert 401 == response.status_code

    def test_put_default_config_secrets_wrong_scope(
        self, api_client: TestClient, payload, url, generate_auth_header
    ):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_put_default_config_secret_invalid_config(
        self, api_client: TestClient, payload, generate_auth_header
    ):
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        url = (V1_URL_PREFIX + STORAGE_DEFAULT_SECRETS).format(
            storage_type="invalid_type"
        )
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 422 == response.status_code

    def test_update_default_with_invalid_secrets_key(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.put(
            url + "?verify=False", headers=auth_header, json={"bad_key": "12345"}
        )

        assert response.json()["detail"] == [
            "Field required ('aws_access_key_id',)",
            "Field required ('aws_secret_access_key',)",
            "Extra inputs are not permitted ('bad_key',)",
        ]
        assert response.status_code == 400

    @mock.patch("fides.api.models.storage.StorageConfig.set_secrets")
    def test_update_default_set_secrets_error(
        self,
        set_secrets_mock: Mock,
        api_client: TestClient,
        generate_auth_header,
        url,
        payload,
    ):
        set_secrets_mock.side_effect = ValueError(
            "This object must have a `type` to validate secrets."
        )
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.put(
            url + "?verify=False", headers=auth_header, json=payload
        )
        assert response.status_code == 400

    def test_put_default_config_secrets_without_verifying(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
        storage_config_default,
    ):
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.put(
            url + "?verify=False", headers=auth_header, json=payload
        )
        assert 200 == response.status_code

        db.refresh(storage_config_default)

        assert json.loads(response.text) == {
            "msg": "Secrets updated for default config of storage type: s3.",
            "test_status": None,
            "failure_reason": None,
        }
        assert (
            storage_config_default.secrets[StorageSecrets.AWS_ACCESS_KEY_ID.value]
            == "1345234524"
        )
        assert (
            storage_config_default.secrets[StorageSecrets.AWS_SECRET_ACCESS_KEY.value]
            == "23451345834789"
        )

    @mock.patch("fides.api.api.v1.endpoints.storage_endpoints.secrets_are_valid")
    def test_put_default_config_secrets_and_verify(
        self,
        mock_valid: Mock,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
        storage_config_default,
    ):
        mock_valid.return_value = True
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        db.refresh(storage_config_default)

        assert json.loads(response.text) == {
            "msg": "Secrets updated for default config of storage type: s3.",
            "test_status": "succeeded",
            "failure_reason": None,
        }
        assert (
            storage_config_default.secrets[StorageSecrets.AWS_ACCESS_KEY_ID.value]
            == "1345234524"
        )
        assert (
            storage_config_default.secrets[StorageSecrets.AWS_SECRET_ACCESS_KEY.value]
            == "23451345834789"
        )

        mock_valid.reset_mock()
        mock_valid.return_value = False
        response = api_client.put(url, headers=auth_header, json=payload)
        assert json.loads(response.text) == {
            "msg": "Secrets updated for default config of storage type: s3.",
            "test_status": "failed",
            "failure_reason": None,
        }

    @mock.patch(
        "fides.api.service.storage.storage_authenticator_service.get_aws_session"
    )
    def test_put_default_s3_config_secrets_and_verify(
        self,
        get_aws_session_mock: Mock,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code
        get_aws_session_mock.assert_called_once_with(
            AWSAuthMethod.SECRET_KEYS.value,
            {
                "aws_access_key_id": payload["aws_access_key_id"],
                "aws_secret_access_key": payload["aws_secret_access_key"],
            },
        )


class TestGetActiveDefaultStorageConfig:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + STORAGE_ACTIVE_DEFAULT

    def test_get_active_default_config_not_authenticated(
        self, url, api_client: TestClient
    ):
        response = api_client.get(url)
        assert 401 == response.status_code

    def test_get_active_default_config_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header([STORAGE_DELETE])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_get_active_default_none_set(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        retrieved_config = response.json()
        assert retrieved_config["type"] == StorageType.local.value
        assert retrieved_config["name"] == default_storage_config_name(
            StorageType.local.value
        )
        assert retrieved_config["is_default"]

    def test_get_active_default_app_setting_not_set(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        storage_config_default,
    ):
        """
        Even with `storage_config_default` fixture creating a default s3 storage,
        we should still get the fallback local config as the active default
        since the application setting for "active default" storage is not yet set
        """
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        retrieved_config = response.json()
        assert retrieved_config["type"] == StorageType.local.value
        assert retrieved_config["name"] == default_storage_config_name(
            StorageType.local.value
        )
        assert retrieved_config["is_default"]

    @pytest.mark.usefixtures("set_active_storage_s3")
    def test_get_active_default_app_setting_but_not_configured(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        """
        Without `storage_config_default` fixture creating a default s3 storage,
        but by setting the application setting for "active default" storage to s3,
        we should get a 404, since we have no s3 default storage configured.
        """
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 404 == response.status_code

    @pytest.mark.usefixtures("set_active_storage_s3")
    def test_get_active_default_config(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        storage_config_default: StorageConfig,
    ):
        """
        We should get back our s3 storage config default now that
        we set s3 as the active default storage via app setting
        """
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200

        response_body = response.json()

        assert response_body == {
            "name": storage_config_default.name,
            "type": storage_config_default.type.value,
            "details": {
                "auth_method": storage_config_default.details["auth_method"],
                "naming": storage_config_default.details["naming"],
                "bucket": "test_bucket",
            },
            "key": storage_config_default.key,
            "format": storage_config_default.format.value,
            "is_default": True,
        }


class TestGetStorageStatus:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + STORAGE_STATUS

    def test_get_storage_status_not_authenticated(self, url, api_client: TestClient):
        response = api_client.get(url)
        assert 401 == response.status_code

    def test_get_storage_status_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header([STORAGE_DELETE])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_get_storage_status_none_set(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        response = StorageConfigStatusMessage(**response.json())
        assert response.config_status == StorageConfigStatus.not_configured
        assert (
            response.detail
            == "Active default storage configuration is not one of the fully configured storage types"
        )

    def test_get_storage_status_app_setting_not_set(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        storage_config_default,
    ):
        """
        Even with `storage_config` fixture creating a default s3 storage config,
        we should still not get a successful status reading, since the
        `storage.active_default_storage_type` config property has not been set
        and therefore we default to local storage

        """
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        response = StorageConfigStatusMessage(**response.json())
        assert response.config_status == StorageConfigStatus.not_configured
        assert (
            response.detail
            == "Active default storage configuration is not one of the fully configured storage types"
        )

    @pytest.fixture(scope="function")
    def active_default_storage_s3(self, db, config_proxy: ConfigProxy):
        """Set s3 as the `active_default_storage_type` property"""
        original_value = config_proxy.storage.active_default_storage_type
        ApplicationConfig.update_api_set(
            db, {"storage": {"active_default_storage_type": StorageType.s3.value}}
        )
        yield
        ApplicationConfig.update_api_set(
            db, {"storage": {"active_default_storage_type": original_value}}
        )

    @pytest.fixture(scope="function")
    def active_default_storage_local(self, db, config_proxy: ConfigProxy):
        """Set local as the `active_default_storage_type` property"""
        original_value = config_proxy.storage.active_default_storage_type
        ApplicationConfig.update_api_set(
            db, {"storage": {"active_default_storage_type": StorageType.local.value}}
        )
        yield
        ApplicationConfig.update_api_set(
            db, {"storage": {"active_default_storage_type": original_value}}
        )

    @pytest.mark.usefixtures("active_default_storage_local", "storage_config_default")
    def test_get_storage_status_app_setting_wrong_value(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        """
        Even with `storage_config_default` fixture creating a default storage config,
        we should still not get a successful status reading, since the
        `storage.active_default_storage_type` config property has been set to
        `local` and it needs to be set to s3 for storage to be considered
        successfully configured

        """
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        response = StorageConfigStatusMessage(**response.json())
        assert response.config_status == StorageConfigStatus.not_configured
        assert (
            response.detail
            == "Active default storage configuration is not one of the fully configured storage types"
        )

    @pytest.mark.usefixtures(
        "active_default_storage_local", "storage_config_default_local"
    )
    def test_get_storage_status_app_setting_not_s3(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        """
        Even with `storage_config_default_local` fixture creating a default local storage config,
        we should still not get a successful status reading, since the
        `storage.active_default_storage_type` config property has been set to
        `local` and only s3 storage configs are considered fully "configured"

        """
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        response = StorageConfigStatusMessage(**response.json())
        assert response.config_status == StorageConfigStatus.not_configured
        assert (
            response.detail
            == "Active default storage configuration is not one of the fully configured storage types"
        )

    @pytest.mark.usefixtures("active_default_storage_s3")
    def test_get_storage_status_app_setting_but_not_configured(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        """
        Without `storage_config_default` fixture creating a default storage config,
        but by setting the application setting for `active_default_storage_type` to s3,
        we should get a failure, since we have no s3 default configured.
        """
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        response = StorageConfigStatusMessage(**response.json())
        assert response.config_status == StorageConfigStatus.not_configured
        assert response.detail == "No active default storage configuration found"

    @pytest.mark.usefixtures(
        "active_default_storage_s3", "storage_config_default_s3_secret_keys"
    )
    def test_get_storage_status_secrets_not_present(
        self,
        url,
        db: Session,
        api_client: TestClient,
        generate_auth_header,
    ):
        """
        If secrets aren't present on the s3 default config, we should get a failure
        """
        storage_config = db.query(StorageConfig).first()
        storage_config.secrets = {}
        storage_config.save(db)

        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        response = StorageConfigStatusMessage(**response.json())
        assert response.config_status == StorageConfigStatus.not_configured
        assert "No secrets found" in response.detail

    @pytest.mark.usefixtures(
        "active_default_storage_s3", "storage_config_default_s3_secret_keys"
    )
    def test_get_storage_status_wrong_secrets(
        self,
        url,
        db: Session,
        api_client: TestClient,
        generate_auth_header,
    ):
        """
        If invalid secrets are somehow present on the s3 default config, we should get a failure
        """
        storage_config = db.query(StorageConfig).first()
        storage_config.secrets = {"invalid_secret": "invalid"}
        storage_config.save(db)

        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        response = StorageConfigStatusMessage(**response.json())
        assert response.config_status == StorageConfigStatus.not_configured
        assert "Invalid secrets found" in response.detail

    @pytest.mark.usefixtures("active_default_storage_s3", "storage_config_default")
    def test_get_storage_status_details_not_present(
        self,
        url,
        db: Session,
        api_client: TestClient,
        generate_auth_header,
    ):
        """
        If details aren't present on the default storage config, we should get a failure
        """
        storage_config = db.query(StorageConfig).first()
        storage_config.details = {}
        storage_config.save(db)

        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        response = StorageConfigStatusMessage(**response.json())
        assert response.config_status == StorageConfigStatus.not_configured
        assert "Invalid or unpopulated details" in response.detail

    @pytest.mark.usefixtures("active_default_storage_s3", "storage_config_default")
    def test_get_storage_status_details_wrong_values(
        self,
        url,
        db: Session,
        api_client: TestClient,
        generate_auth_header,
    ):
        """
        If wrong details are on the storage config, we should get a failure
        """
        storage_config = db.query(StorageConfig).first()
        storage_config.details = {"invalid": "invalid"}
        storage_config.save(db)

        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        response = StorageConfigStatusMessage(**response.json())
        assert response.config_status == StorageConfigStatus.not_configured
        assert "Invalid or unpopulated details" in response.detail

    @pytest.mark.usefixtures("active_default_storage_s3", "storage_config_default")
    def test_get_storage_status(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        """
        We should get back a successful response now that
        we set s3 as the `active_default_storage_type` via app setting
        and the config has been added via fixture
        """
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        response = StorageConfigStatusMessage(**response.json())
        assert response.config_status == StorageConfigStatus.configured
        assert StorageType.s3.value in (response.detail)

    @pytest.mark.usefixtures(
        "active_default_storage_s3", "storage_config_default_s3_secret_keys"
    )
    def test_get_storage_status_s3_secret_keys(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        """
        We should get back a successful response now that
        we set s3 as the `active_default_storage_type` via app setting
        and the config has been added via fixture
        """
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        response = StorageConfigStatusMessage(**response.json())
        assert response.config_status == StorageConfigStatus.configured
        assert StorageType.s3.value in (response.detail)
