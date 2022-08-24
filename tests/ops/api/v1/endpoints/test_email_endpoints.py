import json

import pytest
from fastapi_pagination import Params
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fides.api.ops.api.v1.scope_registry import (
    EMAIL_CREATE_OR_UPDATE,
    EMAIL_DELETE,
    EMAIL_READ,
)
from fides.api.ops.api.v1.urn_registry import (
    EMAIL_BY_KEY,
    EMAIL_CONFIG,
    EMAIL_SECRETS,
    V1_URL_PREFIX,
)
from fides.api.ops.models.email import EmailConfig
from fides.api.ops.schemas.email.email import (
    EmailServiceDetails,
    EmailServiceSecrets,
    EmailServiceType,
)

PAGE_SIZE = Params().size


class TestPostEmailConfig:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + EMAIL_CONFIG

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            "name": "mailgun",
            "service_type": EmailServiceType.MAILGUN.value,
            "details": {EmailServiceDetails.DOMAIN.value: "my.mailgun.domain"},
        }

    def test_post_email_config_not_authenticated(
        self, api_client: TestClient, payload, url
    ):
        response = api_client.post(url, headers={}, json=payload)
        assert 401 == response.status_code

    def test_post_email_config_incorrect_scope(
        self,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([EMAIL_READ])
        response = api_client.post(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_post_email_config_with_invalid_mailgun_details(
        self,
        db: Session,
        api_client: TestClient,
        url,
        payload,
        generate_auth_header,
    ):
        payload["details"] = {"invalid": "invalid"}

        auth_header = generate_auth_header([EMAIL_CREATE_OR_UPDATE])
        response = api_client.post(url, headers=auth_header, json=payload)
        assert 422 == response.status_code
        assert json.loads(response.text)["detail"][0]["msg"] == "field required"
        assert (
            json.loads(response.text)["detail"][1]["msg"]
            == "extra fields not permitted"
        )

    def test_post_email_config_with_not_supported_service_type(
        self,
        db: Session,
        api_client: TestClient,
        url,
        payload,
        generate_auth_header,
    ):
        payload["service_type"] = "twilio"

        auth_header = generate_auth_header([EMAIL_CREATE_OR_UPDATE])
        response = api_client.post(url, headers=auth_header, json=payload)
        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "value is not a valid enumeration member; permitted: 'mailgun'"
        )

    def test_post_email_config_with_no_key(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([EMAIL_CREATE_OR_UPDATE])
        response = api_client.post(url, headers=auth_header, json=payload)

        assert 200 == response.status_code
        response_body = json.loads(response.text)

        assert response_body["key"] == "mailgun"
        email_config = db.query(EmailConfig).filter_by(key="mailgun")[0]
        email_config.delete(db)

    def test_post_email_config_with_invalid_key(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        payload["key"] = "*invalid-key"
        auth_header = generate_auth_header([EMAIL_CREATE_OR_UPDATE])
        response = api_client.post(url, headers=auth_header, json=payload)
        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "FidesKey must only contain alphanumeric characters, '.', '_' or '-'."
        )

    def test_post_email_config_with_key(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        payload["key"] = "my_email_config"
        auth_header = generate_auth_header([EMAIL_CREATE_OR_UPDATE])

        response = api_client.post(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        response_body = json.loads(response.text)
        email_config = db.query(EmailConfig).filter_by(key="my_email_config")[0]

        expected_response = {
            "key": "my_email_config",
            "name": "mailgun",
            "service_type": EmailServiceType.MAILGUN.value,
            "details": {
                EmailServiceDetails.API_VERSION.value: "v3",
                EmailServiceDetails.DOMAIN.value: "my.mailgun.domain",
                EmailServiceDetails.IS_EU_DOMAIN.value: False,
            },
        }
        assert expected_response == response_body
        email_config.delete(db)

    def test_post_email_config_missing_detail(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([EMAIL_CREATE_OR_UPDATE])
        response = api_client.post(
            url,
            headers=auth_header,
            json={
                "key": "my_email_config",
                "name": "mailgun",
                "service_type": EmailServiceType.MAILGUN.value,
                "details": {
                    # "domain": "my.mailgun.domain"
                },
            },
        )
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert "details" in errors[0]["loc"]
        assert errors[0]["msg"] == "field required"

    def test_post_email_config_already_exists(
        self,
        api_client: TestClient,
        url,
        email_config,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([EMAIL_CREATE_OR_UPDATE])
        response = api_client.post(
            url,
            headers=auth_header,
            json={
                "key": "my_email_config",
                "name": "mailgun",
                "service_type": EmailServiceType.MAILGUN.value,
                "details": {EmailServiceDetails.DOMAIN.value: "my.mailgun.domain"},
            },
        )
        assert response.status_code == 400
        assert response.json() == {
            "detail": "Only one email config is supported at a time. Config with key my_email_config is already configured."
        }


class TestPatchEmailConfig:
    @pytest.fixture(scope="function")
    def url(self, email_config) -> str:
        return (V1_URL_PREFIX + EMAIL_BY_KEY).format(config_key=email_config.key)

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            "key": "my_email_config",
            "name": "mailgun new name",
            "service_type": EmailServiceType.MAILGUN.value,
            "details": {EmailServiceDetails.DOMAIN.value: "my.mailgun.domain"},
        }

    def test_patch_email_config_not_authenticated(
        self, api_client: TestClient, payload, url
    ):
        response = api_client.patch(url, headers={}, json=payload)
        assert 401 == response.status_code

    def test_patch_email_config_incorrect_scope(
        self,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([EMAIL_READ])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_patch_email_config_with_key_not_found(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        email_config,
        generate_auth_header,
    ):
        url = (V1_URL_PREFIX + EMAIL_BY_KEY).format(config_key="nonexistent_key")
        auth_header = generate_auth_header([EMAIL_CREATE_OR_UPDATE])

        response = api_client.patch(url, headers=auth_header, json=payload)
        assert response.status_code == 404
        assert response.json() == {
            "detail": "No email config found with key nonexistent_key"
        }

    def test_patch_email_config_with_key(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([EMAIL_CREATE_OR_UPDATE])

        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        response_body = json.loads(response.text)
        email_config = db.query(EmailConfig).filter_by(key="my_email_config")[0]

        expected_response = {
            "key": "my_email_config",
            "name": "mailgun new name",
            "service_type": EmailServiceType.MAILGUN.value,
            "details": {
                EmailServiceDetails.API_VERSION.value: "v3",
                EmailServiceDetails.DOMAIN.value: "my.mailgun.domain",
                EmailServiceDetails.IS_EU_DOMAIN.value: False,
            },
        }
        assert expected_response == response_body
        email_config.delete(db)


class TestPutEmailConfigSecretsMailgun:
    @pytest.fixture(scope="function")
    def url(self, email_config) -> str:
        return (V1_URL_PREFIX + EMAIL_SECRETS).format(config_key=email_config.key)

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            EmailServiceSecrets.MAILGUN_API_KEY.value: "1345234524",
        }

    def test_put_config_secrets_unauthenticated(
        self, api_client: TestClient, payload, url
    ):
        response = api_client.put(url, headers={}, json=payload)
        assert 401 == response.status_code

    def test_put_config_secrets_wrong_scope(
        self, api_client: TestClient, payload, url, generate_auth_header
    ):
        auth_header = generate_auth_header([EMAIL_READ])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_put_config_secret_invalid_config(
        self, api_client: TestClient, payload, generate_auth_header
    ):
        auth_header = generate_auth_header([EMAIL_CREATE_OR_UPDATE])
        url = (V1_URL_PREFIX + EMAIL_SECRETS).format(config_key="invalid_key")
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 404 == response.status_code

    def test_update_with_invalid_secrets_key(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header([EMAIL_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json={"bad_key": "12345"})

        assert response.status_code == 400
        assert response.json() == {
            "detail": [
                "field required ('mailgun_api_key',)",
                "extra fields not permitted ('bad_key',)",
            ]
        }

    def test_put_config_secrets(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
        email_config,
    ):
        auth_header = generate_auth_header([EMAIL_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        db.refresh(email_config)

        assert json.loads(response.text) == {
            "msg": "Secrets updated for EmailConfig with key: my_email_config.",
            "test_status": None,
            "failure_reason": None,
        }
        assert (
            email_config.secrets[EmailServiceSecrets.MAILGUN_API_KEY.value]
            == "1345234524"
        )


class TestGetEmailConfigs:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + EMAIL_CONFIG

    def test_get_configs_not_authenticated(self, api_client: TestClient, url) -> None:
        response = api_client.get(url)
        assert 401 == response.status_code

    def test_get_configs_wrong_scope(
        self, api_client: TestClient, url, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header([EMAIL_DELETE])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_get_configs(
        self, db, api_client: TestClient, url, generate_auth_header, email_config
    ):
        auth_header = generate_auth_header([EMAIL_READ])
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code

        expected_response = {
            "items": [
                {
                    "key": "my_email_config",
                    "name": email_config.name,
                    "service_type": EmailServiceType.MAILGUN.value,
                    "details": {
                        EmailServiceDetails.API_VERSION.value: "v3",
                        EmailServiceDetails.DOMAIN.value: "some.domain",
                        EmailServiceDetails.IS_EU_DOMAIN.value: False,
                    },
                }
            ],
            "page": 1,
            "size": PAGE_SIZE,
            "total": 1,
        }
        response_body = json.loads(response.text)
        assert expected_response == response_body


class TestGetEmailConfig:
    @pytest.fixture(scope="function")
    def url(self, email_config) -> str:
        return (V1_URL_PREFIX + EMAIL_BY_KEY).format(config_key=email_config.key)

    def test_get_config_not_authenticated(self, url, api_client: TestClient):
        response = api_client.get(url)
        assert 401 == response.status_code

    def test_get_config_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header([EMAIL_DELETE])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_get_config_invalid(
        self, api_client: TestClient, generate_auth_header, email_config
    ):
        auth_header = generate_auth_header([EMAIL_READ])
        response = api_client.get(
            (V1_URL_PREFIX + EMAIL_BY_KEY).format(config_key="invalid"),
            headers=auth_header,
        )
        assert 404 == response.status_code

    def test_get_config(
        self, url, api_client: TestClient, generate_auth_header, email_config
    ):
        auth_header = generate_auth_header([EMAIL_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200

        response_body = json.loads(response.text)

        assert response_body == {
            "key": "my_email_config",
            "name": email_config.name,
            "service_type": EmailServiceType.MAILGUN.value,
            "details": {
                EmailServiceDetails.API_VERSION.value: "v3",
                EmailServiceDetails.DOMAIN.value: "some.domain",
                EmailServiceDetails.IS_EU_DOMAIN.value: False,
            },
        }


class TestDeleteConfig:
    @pytest.fixture(scope="function")
    def url(self, email_config) -> str:
        return (V1_URL_PREFIX + EMAIL_BY_KEY).format(config_key=email_config.key)

    def test_delete_config_not_authenticated(self, url, api_client: TestClient):
        response = api_client.delete(url)
        assert 401 == response.status_code

    def test_delete_config_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header([EMAIL_READ])
        response = api_client.delete(url, headers=auth_header)
        assert 403 == response.status_code

    def test_delete_config_invalid(self, api_client: TestClient, generate_auth_header):
        auth_header = generate_auth_header([EMAIL_DELETE])
        response = api_client.delete(
            (V1_URL_PREFIX + EMAIL_BY_KEY).format(config_key="invalid"),
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
        email_config = EmailConfig.create(
            db=db,
            data={
                "key": "my_different_email_config",
                "name": "mailgun",
                "service_type": EmailServiceType.MAILGUN,
                "details": {EmailServiceDetails.DOMAIN.value: "my.mailgun.domain"},
            },
        )
        url = (V1_URL_PREFIX + EMAIL_BY_KEY).format(config_key=email_config.key)
        auth_header = generate_auth_header([EMAIL_DELETE])
        response = api_client.delete(url, headers=auth_header)
        assert response.status_code == 204

        db.expunge_all()
        config = db.query(EmailConfig).filter_by(key=email_config.key).first()
        assert config is None
