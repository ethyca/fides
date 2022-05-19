import json
from typing import Dict
from unittest import mock
from unittest.mock import Mock

import pytest
from fastapi_pagination import Params
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fidesops.api.v1.scope_registry import (
    STORAGE_CREATE_OR_UPDATE,
    STORAGE_DELETE,
    STORAGE_READ,
)
from fidesops.api.v1.urn_registry import (
    STORAGE_BY_KEY,
    STORAGE_CONFIG,
    STORAGE_SECRETS,
    STORAGE_UPLOAD,
    V1_URL_PREFIX,
)
from fidesops.models.client import ClientDetail
from fidesops.models.storage import StorageConfig
from fidesops.schemas.storage.data_upload_location_response import DataUpload
from fidesops.schemas.storage.storage import (
    FileNaming,
    ResponseFormat,
    StorageDetails,
    StorageSecrets,
    StorageType,
)

PAGE_SIZE = Params().size


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

    @mock.patch("fidesops.api.v1.endpoints.storage_endpoints.upload")
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
            request_id=privacy_request.id,
            data=payload.get("data"),
            storage_key=payload.get("storage_key"),
        )
        assert response_body == DataUpload(location=expected_location)


class TestPatchStorageConfig:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail) -> str:
        return V1_URL_PREFIX + STORAGE_CONFIG

    @pytest.fixture(scope="function")
    def payload(self):
        return [
            {
                "name": "test destination",
                "type": "s3",
                "details": {
                    "bucket": "some-bucket",
                    "object_name": "requests",
                    "naming": "some-filename-convention-enum",
                    "max_retries": 10,
                },
                "format": "csv",
            }
        ]

    @mock.patch(
        "fidesops.api.v1.endpoints.storage_endpoints.initiate_scheduled_request_intake"
    )
    def test_patch_storage_config_not_authenticated(
        self, mock_scheduled_task, api_client: TestClient, payload, url
    ):
        mock_scheduled_task.return_value = None
        response = api_client.patch(url, headers={}, json=payload)
        assert 401 == response.status_code
        mock_scheduled_task.assert_not_called()

    @mock.patch(
        "fidesops.api.v1.endpoints.storage_endpoints.initiate_scheduled_request_intake"
    )
    def test_patch_storage_config_incorrect_scope(
        self,
        mock_scheduled_task,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 403 == response.status_code
        mock_scheduled_task.assert_not_called()

    def test_patch_storage_config_with_onetrust_format_conflict(
        self,
        db: Session,
        api_client: TestClient,
        url,
        generate_auth_header,
    ):
        payload = [
            {
                "name": "my test destination",
                "type": "onetrust",
                "details": {
                    "service_name": "a-service",
                    "onetrust_polling_hr": 1,
                    "onetrust_polling_day_of_week": 1,
                },
                "format": "csv",
            }
        ]

        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "Only JSON upload format is supported for OneTrust and local storage destinations."
        )

    @mock.patch(
        "fidesops.api.v1.endpoints.storage_endpoints.initiate_scheduled_request_intake"
    )
    def test_patch_storage_config_with_no_key(
        self,
        mock_scheduled_task,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.patch(url, headers=auth_header, json=payload)

        assert 200 == response.status_code
        mock_scheduled_task.assert_called()
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
            == "FidesKey must only contain alphanumeric characters, '.' or '_'."
        )

    @mock.patch(
        "fidesops.api.v1.endpoints.storage_endpoints.initiate_scheduled_request_intake"
    )
    def test_patch_storage_configs_limits_exceeded(
        self,
        _,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):

        payload = []
        for i in range(0, 51):
            payload.append(
                {
                    "name": f"my test destination {i}",
                    "type": "onetrust",
                    "details": {
                        "bucket": "some-bucket",
                        "object_name": "requests",
                        "naming": "some-filename-convention-enum",
                        "max_retries": 10,
                    },
                    "format": "csv",
                }
            )

        auth_header = generate_auth_header(scopes=[STORAGE_CREATE_OR_UPDATE])
        response = api_client.patch(url, headers=auth_header, json=payload)

        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "ensure this value has at most 50 items"
        )

    @mock.patch(
        "fidesops.api.v1.endpoints.storage_endpoints.initiate_scheduled_request_intake"
    )
    def test_patch_storage_config_with_key(
        self,
        mock_scheduled_task,
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
        mock_scheduled_task.assert_called()

        response_body = json.loads(response.text)
        mock_scheduled_task.assert_called()
        storage_config = db.query(StorageConfig).filter_by(key="my_s3_bucket")[0]

        expected_response = {
            "succeeded": [
                {
                    "name": "test destination",
                    "type": "s3",
                    "details": {
                        "bucket": "some-bucket",
                        "naming": "some-filename-convention-enum",
                        "max_retries": 10,
                        "object_name": "requests",
                    },
                    "key": "my_s3_bucket",
                    "format": "csv",
                }
            ],
            "failed": [],
        }
        assert expected_response == response_body
        storage_config.delete(db)

    @mock.patch(
        "fidesops.api.v1.endpoints.storage_endpoints.initiate_scheduled_request_intake"
    )
    def test_patch_config_response_format_not_specified(
        self,
        mock_scheduled_task: Mock,
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
                "type": "s3",
                "details": {
                    "bucket": "some-bucket",
                    "object_name": "requests",
                    "naming": "some-filename-convention-enum",
                    "max_retries": 10,
                },
            }
        ]
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        mock_scheduled_task.return_value = None

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
                    "key": "my_onetrust_upload",
                    "name": "my-test-dest",
                    "type": "s3",
                    "details": {
                        # "bucket": "removed-from-payload",
                        "object_name": "some-object",
                        "naming": "request_id",
                        "max_retries": 10,
                    },
                },
            ],
        )
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert "details" in errors[0]["loc"]
        assert errors[0]["msg"] == "[\"field required ('bucket',)\"]"


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

    @pytest.fixture(scope="function")
    def onetrust_url(self, storage_config_onetrust) -> str:
        return (V1_URL_PREFIX + STORAGE_SECRETS).format(
            config_key=storage_config_onetrust.key
        )

    @pytest.fixture(scope="function")
    def onetrust_payload(self):
        return {
            StorageSecrets.ONETRUST_CLIENT_ID.value: "1345234524",
            StorageSecrets.ONETRUST_CLIENT_SECRET.value: "23451345834789",
            StorageSecrets.ONETRUST_HOSTNAME.value: "a-hostname",
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
        assert response.json() == {
            "detail": [
                "field required ('aws_access_key_id',)",
                "field required ('aws_secret_access_key',)",
                "extra fields not permitted ('bad_key',)",
            ]
        }

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

    @mock.patch("fidesops.api.v1.endpoints.storage_endpoints.secrets_are_valid")
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

    @mock.patch("fidesops.service.storage.storage_authenticator_service.get_s3_session")
    def test_put_s3_config_secrets_and_verify(
        self,
        get_s3_session_mock: Mock,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code
        get_s3_session_mock.assert_called_once_with(**payload)

    @mock.patch(
        "fidesops.service.storage.storage_authenticator_service.get_onetrust_access_token"
    )
    def test_put_onetrust_config_secrets_and_verify(
        self,
        get_onetrust_access_token_mock: Mock,
        api_client: TestClient,
        onetrust_payload,
        onetrust_url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.put(
            onetrust_url, headers=auth_header, json=onetrust_payload
        )
        assert 200 == response.status_code
        get_onetrust_access_token_mock.assert_called_once_with(
            client_id=onetrust_payload[StorageSecrets.ONETRUST_CLIENT_ID.value],
            client_secret=onetrust_payload[StorageSecrets.ONETRUST_CLIENT_SECRET.value],
            hostname=onetrust_payload[StorageSecrets.ONETRUST_HOSTNAME.value],
        )


class TestPutStorageConfigSecretsOneTrust:
    @pytest.fixture(scope="function")
    def url(self, storage_config_onetrust) -> str:
        return (V1_URL_PREFIX + STORAGE_SECRETS).format(
            config_key=storage_config_onetrust.key
        )

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            StorageSecrets.ONETRUST_CLIENT_ID.value: "23iutby1oiur",
            StorageSecrets.ONETRUST_CLIENT_SECRET.value: "23i4bty1i3urhnlw",
            StorageSecrets.ONETRUST_HOSTNAME.value: "peanutbutter.onetrust",
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

    def test_put_config_secrets_without_verifying(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
        storage_config_onetrust,
    ):
        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.put(
            url + "?verify=False", headers=auth_header, json=payload
        )
        assert 200 == response.status_code

        db.refresh(storage_config_onetrust)

        assert json.loads(response.text) == {
            "msg": f"Secrets updated for StorageConfig with key: {storage_config_onetrust.key}.",
            "test_status": None,
            "failure_reason": None,
        }
        assert (
            storage_config_onetrust.secrets[StorageSecrets.ONETRUST_CLIENT_ID.value]
            == "23iutby1oiur"
        )
        assert (
            storage_config_onetrust.secrets[StorageSecrets.ONETRUST_CLIENT_SECRET.value]
            == "23i4bty1i3urhnlw"
        )
        assert (
            storage_config_onetrust.secrets[StorageSecrets.ONETRUST_HOSTNAME.value]
            == "peanutbutter.onetrust"
        )

    @mock.patch("fidesops.api.v1.endpoints.storage_endpoints.secrets_are_valid")
    def test_put_config_secrets_and_verify(
        self,
        mock_valid: Mock,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
        storage_config_onetrust,
    ):
        mock_valid.return_value = True

        auth_header = generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        db.refresh(storage_config_onetrust)

        assert json.loads(response.text) == {
            "msg": f"Secrets updated for StorageConfig with key: {storage_config_onetrust.key}.",
            "test_status": "succeeded",
            "failure_reason": None,
        }
        assert (
            storage_config_onetrust.secrets[StorageSecrets.ONETRUST_CLIENT_ID.value]
            == "23iutby1oiur"
        )
        assert (
            storage_config_onetrust.secrets[StorageSecrets.ONETRUST_CLIENT_SECRET.value]
            == "23i4bty1i3urhnlw"
        )
        assert (
            storage_config_onetrust.secrets[StorageSecrets.ONETRUST_HOSTNAME.value]
            == "peanutbutter.onetrust"
        )

        mock_valid.reset_mock()
        mock_valid.return_value = False
        response = api_client.put(url, headers=auth_header, json=payload)
        assert json.loads(response.text) == {
            "msg": f"Secrets updated for StorageConfig with key: {storage_config_onetrust.key}.",
            "test_status": "failed",
            "failure_reason": None,
        }

    def test_put_storage_secrets_invalid_keys(
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
                # StorageSecrets.ONETRUST_CLIENT_ID.value: "removed-from-payload",
                StorageSecrets.ONETRUST_CLIENT_SECRET.value: "23i4bty1i3urhnlw",
                StorageSecrets.ONETRUST_HOSTNAME.value: "peanutbutter.onetrust",
            },
        )

        assert 400 == response.status_code
        assert response.json()["detail"] == ["field required ('onetrust_client_id',)"]


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
                    "details": {"bucket": "test_bucket", "naming": "request_id"},
                    "format": "json",
                }
            ],
            "page": 1,
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
            "type": "s3",
            "details": {"bucket": "test_bucket", "naming": "request_id"},
            "key": "my_test_config",
            "format": "json",
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
