import json
from unittest import mock

import pytest
from fastapi_pagination import Params

from fides.api.ops.api.v1.scope_registry import (
    STORAGE_CREATE_OR_UPDATE,
    STORAGE_DELETE,
    STORAGE_READ,
)
from fides.api.ops.api.v1.urn_registry import (
    STORAGE_BY_KEY,
    STORAGE_CONFIG,
    STORAGE_SECRETS,
    STORAGE_UPLOAD,
    V1_URL_PREFIX,
)
from fides.api.ops.models.storage import StorageConfig
from fides.api.ops.schemas.storage.data_upload_location_response import DataUpload
from fides.api.ops.schemas.storage.storage import (
    FileNaming,
    ResponseFormat,
    S3AuthMethod,
    StorageDetails,
    StorageSecrets,
    StorageType,
)

PAGE_SIZE = Params().size


class TestUploadData:
    @pytest.fixture(scope="function")
    def url(self, privacy_request):
        return (V1_URL_PREFIX + STORAGE_UPLOAD).format(request_id=privacy_request.id)

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            "storage_key": "s3_destination_key",
            "data": {
                "email": "email@gmail.com",
                "address": "123 main ST, Asheville NC",
                "zip codes": [12345, 54321],
            },
        }

    def test_upload_data_not_authenticated(self, url, api_client, payload):
        response = api_client.post(url, headers={}, json=payload)
        assert 401 == response.status_code

    @pytest.mark.parametrize("auth_header", [[STORAGE_READ]], indirect=True)
    def test_upload_data_wrong_scope(self, auth_header, url, api_client, payload):
        response = api_client.post(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    @pytest.mark.parametrize("auth_header", [[STORAGE_CREATE_OR_UPDATE]], indirect=True)
    def test_invalid_privacy_request(self, auth_header, api_client, payload):
        url = (V1_URL_PREFIX + STORAGE_UPLOAD).format(request_id="invalid-id")
        response = api_client.post(url, headers=auth_header, json=payload)
        assert 404 == response.status_code

    @pytest.mark.parametrize("auth_header", [[STORAGE_CREATE_OR_UPDATE]], indirect=True)
    @mock.patch("fides.api.ops.api.v1.endpoints.storage_endpoints.upload")
    def test_post_upload_data(
        self,
        mock_post_upload_data,
        auth_header,
        api_client,
        url,
        privacy_request,
        payload,
    ):
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
    def url(self):
        return V1_URL_PREFIX + STORAGE_CONFIG

    @pytest.fixture(scope="function")
    def payload(self):
        return [
            {
                "name": "test destination",
                "type": StorageType.s3.value,
                "details": {
                    "auth_method": S3AuthMethod.SECRET_KEYS.value,
                    "bucket": "some-bucket",
                    "naming": "some-filename-convention-enum",
                    "max_retries": 10,
                },
                "format": "csv",
            }
        ]

    def test_patch_storage_config_not_authenticated(
        self,
        api_client,
        payload,
        url,
    ):
        response = api_client.patch(url, headers={}, json=payload)
        assert 401 == response.status_code

    @pytest.mark.parametrize("auth_header", [[STORAGE_READ]], indirect=True)
    def test_patch_storage_config_incorrect_scope(
        self, auth_header, api_client, payload, url
    ):
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    @pytest.mark.parametrize("auth_header", [[STORAGE_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_storage_config_with_no_key(
        self,
        auth_header,
        api_client,
        payload,
        url,
    ):
        response = api_client.patch(url, headers=auth_header, json=payload)

        assert 200 == response.status_code
        response_body = json.loads(response.text)

        assert response_body["succeeded"][0]["key"] == "test_destination"

    @pytest.mark.parametrize("auth_header", [[STORAGE_CREATE_OR_UPDATE]], indirect=True)
    def test_put_storage_config_with_invalid_key(
        self,
        auth_header,
        api_client,
        payload,
        url,
    ):
        payload[0]["key"] = "*invalid-key"
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "FidesKeys must only contain alphanumeric characters, '.', '_', '<', '>' or '-'. Value provided: *invalid-key"
        )

    @pytest.mark.parametrize("auth_header", [[STORAGE_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_storage_config_with_key(self, auth_header, api_client, payload, url):
        payload[0]["key"] = "my_s3_bucket"

        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        response_body = json.loads(response.text)

        expected_response = {
            "succeeded": [
                {
                    "name": "test destination",
                    "type": StorageType.s3.value,
                    "details": {
                        "auth_method": S3AuthMethod.SECRET_KEYS.value,
                        "bucket": "some-bucket",
                        "naming": "some-filename-convention-enum",
                        "max_retries": 10,
                    },
                    "key": "my_s3_bucket",
                    "format": "csv",
                }
            ],
            "failed": [],
        }
        assert expected_response == response_body

    @pytest.mark.parametrize(
        "auth_method", [S3AuthMethod.SECRET_KEYS.value, S3AuthMethod.AUTOMATIC.value]
    )
    @pytest.mark.parametrize("auth_header", [[STORAGE_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_storage_config_with_different_auth_methods(
        self, auth_header, api_client, payload, url, auth_method
    ):
        payload[0]["key"] = "my_s3_bucket"
        payload[0]["details"]["auth_method"] = auth_method
        response = api_client.patch(url, headers=auth_header, json=payload)

        assert 200 == response.status_code
        response_body = json.loads(response.text)
        assert auth_method == response_body["succeeded"][0]["details"]["auth_method"]

    @pytest.mark.parametrize("auth_header", [[STORAGE_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_config_response_format_not_specified(
        self,
        auth_header,
        url,
        api_client,
    ):
        key = "my_s3_upload"
        payload = [
            {
                "key": key,
                "name": "my-test-dest",
                "type": StorageType.s3.value,
                "details": {
                    "auth_method": S3AuthMethod.SECRET_KEYS.value,
                    "bucket": "some-bucket",
                    "naming": "some-filename-convention-enum",
                    "max_retries": 10,
                },
            }
        ]

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

    @pytest.mark.parametrize("auth_header", [[STORAGE_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_storage_config_missing_detail(self, auth_header, api_client, url):
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
                        "auth_method": S3AuthMethod.SECRET_KEYS.value,
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
    def url(self, storage_config):
        return (V1_URL_PREFIX + STORAGE_SECRETS).format(config_key=storage_config.key)

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            StorageSecrets.AWS_ACCESS_KEY_ID.value: "1345234524",
            StorageSecrets.AWS_SECRET_ACCESS_KEY.value: "23451345834789",
        }

    def test_put_config_secrets_unauthenticated(self, api_client, payload, url):
        response = api_client.put(url, headers={}, json=payload)
        assert 401 == response.status_code

    @pytest.mark.parametrize("auth_header", [[STORAGE_READ]], indirect=True)
    def test_put_config_secrets_wrong_scope(
        self, auth_header, api_client, payload, url
    ):
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    @pytest.mark.parametrize("auth_header", [[STORAGE_CREATE_OR_UPDATE]], indirect=True)
    def test_put_config_secret_invalid_config(self, auth_header, api_client, payload):
        url = (V1_URL_PREFIX + STORAGE_SECRETS).format(config_key="invalid_key")
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 404 == response.status_code

    @pytest.mark.parametrize("auth_header", [[STORAGE_CREATE_OR_UPDATE]], indirect=True)
    def test_update_with_invalid_secrets_key(self, auth_header, api_client, url):
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

    @pytest.mark.parametrize("auth_header", [[STORAGE_CREATE_OR_UPDATE]], indirect=True)
    def test_put_config_secrets_without_verifying(
        self, auth_header, db, api_client, payload, url, storage_config
    ):
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

    @pytest.mark.parametrize("auth_header", [[STORAGE_CREATE_OR_UPDATE]], indirect=True)
    @mock.patch("fides.api.ops.api.v1.endpoints.storage_endpoints.secrets_are_valid")
    def test_put_config_secrets_and_verify(
        self, mock_valid, auth_header, db, api_client, payload, url, storage_config
    ):
        mock_valid.return_value = True
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

    @pytest.mark.parametrize("auth_header", [[STORAGE_CREATE_OR_UPDATE]], indirect=True)
    @mock.patch(
        "fides.api.ops.service.storage.storage_authenticator_service.get_s3_session"
    )
    def test_put_s3_config_secrets_and_verify(
        self, get_s3_session_mock, auth_header, api_client, payload, url
    ):
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code
        get_s3_session_mock.assert_called_once_with(
            S3AuthMethod.SECRET_KEYS.value,
            {
                "aws_access_key_id": payload["aws_access_key_id"],
                "aws_secret_access_key": payload["aws_secret_access_key"],
            },
        )


class TestGetStorageConfigs:
    @pytest.fixture(scope="function")
    def url(self):
        return V1_URL_PREFIX + STORAGE_CONFIG

    def test_get_configs_not_authenticated(self, api_client, url):
        response = api_client.get(url)
        assert 401 == response.status_code

    @pytest.mark.parametrize("auth_header", [[STORAGE_DELETE]], indirect=True)
    def test_get_configs_wrong_scope(self, auth_header, api_client, url):
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    @pytest.mark.parametrize("auth_header", [[STORAGE_READ]], indirect=True)
    def test_get_configs(self, auth_header, api_client, url, storage_config):
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code

        expected_response = {
            "items": [
                {
                    "key": "my_test_config",
                    "name": storage_config.name,
                    "type": storage_config.type.value,
                    "details": {
                        "auth_method": S3AuthMethod.SECRET_KEYS.value,
                        "bucket": "test_bucket",
                        "naming": "request_id",
                    },
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
    def url(self, storage_config):
        return (V1_URL_PREFIX + STORAGE_BY_KEY).format(config_key=storage_config.key)

    def test_get_config_not_authenticated(self, url, api_client):
        response = api_client.get(url)
        assert 401 == response.status_code

    @pytest.mark.parametrize("auth_header", [[STORAGE_DELETE]], indirect=True)
    def test_get_config_wrong_scope(self, auth_header, url, api_client):
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    @pytest.mark.usefixtures("storage_config")
    @pytest.mark.parametrize("auth_header", [[STORAGE_READ]], indirect=True)
    def test_get_config_invalid(self, auth_header, api_client):
        response = api_client.get(
            (V1_URL_PREFIX + STORAGE_BY_KEY).format(config_key="invalid"),
            headers=auth_header,
        )
        assert 404 == response.status_code

    @pytest.mark.parametrize("auth_header", [[STORAGE_READ]], indirect=True)
    def test_get_config(self, auth_header, url, api_client, storage_config):
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200

        response_body = json.loads(response.text)

        assert response_body == {
            "name": storage_config.name,
            "type": StorageType.s3.value,
            "details": {
                "auth_method": S3AuthMethod.SECRET_KEYS.value,
                "bucket": "test_bucket",
                "naming": "request_id",
            },
            "key": "my_test_config",
            "format": "json",
        }


class TestDeleteConfig:
    @pytest.fixture(scope="function")
    def url(self, storage_config):
        return (V1_URL_PREFIX + STORAGE_BY_KEY).format(config_key=storage_config.key)

    def test_delete_config_not_authenticated(self, url, api_client):
        response = api_client.delete(url)
        assert 401 == response.status_code

    @pytest.mark.parametrize("auth_header", [[STORAGE_READ]], indirect=True)
    def test_delete_config_wrong_scope(self, auth_header, api_client, url):
        response = api_client.delete(url, headers=auth_header)
        assert 403 == response.status_code

    @pytest.mark.usefixtures("storage_config")
    @pytest.mark.parametrize("auth_header", [[STORAGE_DELETE]], indirect=True)
    def test_delete_config_invalid(self, auth_header, api_client):
        response = api_client.delete(
            (V1_URL_PREFIX + STORAGE_BY_KEY).format(config_key="invalid"),
            headers=auth_header,
        )
        assert 404 == response.status_code

    @pytest.mark.parametrize("auth_header", [[STORAGE_DELETE]], indirect=True)
    def test_delete_config(self, auth_header, db, url, api_client):
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
        response = api_client.delete(url, headers=auth_header)
        assert response.status_code == 204

        db.expunge_all()
        config = db.query(StorageConfig).filter_by(key=storage_config.key).first()
        assert config is None
