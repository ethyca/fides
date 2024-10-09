import json
from typing import Any, Dict, List
from unittest import mock
from unittest.mock import Mock, patch

import pytest
from fastapi_pagination import Params
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.application_config import ApplicationConfig
from fides.api.models.messaging import MessagingConfig
from fides.api.models.messaging_template import (
    DEFAULT_MESSAGING_TEMPLATES,
    MessagingTemplate,
)
from fides.api.schemas.messaging.messaging import (
    BasicMessagingTemplateResponse,
    MessagingActionType,
    MessagingConfigStatus,
    MessagingConfigStatusMessage,
    MessagingServiceDetails,
    MessagingServiceSecrets,
    MessagingServiceType,
    MessagingTemplateDefault,
    MessagingTemplateWithPropertiesSummary,
)
from fides.common.api.scope_registry import (
    MESSAGING_CREATE_OR_UPDATE,
    MESSAGING_DELETE,
    MESSAGING_READ,
    MESSAGING_TEMPLATE_UPDATE,
)
from fides.common.api.v1.urn_registry import (
    BASIC_MESSAGING_TEMPLATES,
    MESSAGING_ACTIVE_DEFAULT,
    MESSAGING_BY_KEY,
    MESSAGING_CONFIG,
    MESSAGING_DEFAULT,
    MESSAGING_DEFAULT_BY_TYPE,
    MESSAGING_DEFAULT_SECRETS,
    MESSAGING_SECRETS,
    MESSAGING_STATUS,
    MESSAGING_TEMPLATE_BY_ID,
    MESSAGING_TEMPLATE_DEFAULT_BY_TEMPLATE_TYPE,
    MESSAGING_TEMPLATES_BY_TEMPLATE_TYPE,
    MESSAGING_TEMPLATES_SUMMARY,
    MESSAGING_TEST_DEPRECATED,
    V1_URL_PREFIX,
)
from fides.config import get_config

PAGE_SIZE = Params().size
CONFIG = get_config()


class TestPostMessagingConfig:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + MESSAGING_CONFIG

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            "name": "mailgun",
            "service_type": MessagingServiceType.mailgun.value,
            "details": {MessagingServiceDetails.DOMAIN.value: "my.mailgun.domain"},
        }

    @pytest.fixture(scope="function")
    def payload_twilio_email(self):
        return {
            "name": "twilio_email",
            "service_type": MessagingServiceType.twilio_email.value,
            "details": {
                MessagingServiceDetails.TWILIO_EMAIL_FROM.value: "test@email.com"
            },
        }

    @pytest.fixture(scope="function")
    def payload_mailchimp_transactional(self):
        return {
            "name": "mailchimp_transactional_email",
            "service_type": MessagingServiceType.mailchimp_transactional.value,
            "details": {
                MessagingServiceDetails.EMAIL_FROM.value: "user@example.com",
            },
        }

    @pytest.fixture(scope="function")
    def payload_twilio_sms(self):
        return {
            "name": "twilio_sms",
            "service_type": MessagingServiceType.twilio_text.value,
        }

    @pytest.fixture(scope="function")
    def payload_twilio_sms_lowered(self):
        return {
            "name": "twilio_sms",
            "service_type": MessagingServiceType.twilio_text.value.lower(),
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
        auth_header = generate_auth_header([MESSAGING_READ])
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

        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.post(url, headers=auth_header, json=payload)
        assert 422 == response.status_code
        assert response.json()["detail"][0]["msg"] == "Field required"
        assert response.json()["detail"][1]["msg"] == "Extra inputs are not permitted"

    def test_post_mailgun_email_config_with_a_twilio_detail(
        self,
        db: Session,
        api_client: TestClient,
        url,
        payload,
        generate_auth_header,
    ):
        # add a twilio detail field to a mailgun request, should receive a validation error
        payload["details"] = {"twilio_email_from": "invalid"}

        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.post(url, headers=auth_header, json=payload)
        assert 422 == response.status_code
        assert response.json()["detail"][0]["msg"] == "Field required"
        assert response.json()["detail"][1]["msg"] == "Extra inputs are not permitted"

    def test_post_email_config_with_not_supported_service_type(
        self,
        db: Session,
        api_client: TestClient,
        url,
        payload,
        generate_auth_header,
    ):
        payload["service_type"] = "twilio"

        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.post(url, headers=auth_header, json=payload)
        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "Input should be 'mailgun', 'twilio_text', 'twilio_email' or 'mailchimp_transactional'"
        )

    def test_post_email_config_with_no_key(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.post(url, headers=auth_header, json=payload)

        assert 200 == response.status_code
        response_body = json.loads(response.text)

        assert response_body["key"] == "mailgun"
        email_config = db.query(MessagingConfig).filter_by(key="mailgun")[0]
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
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.post(url, headers=auth_header, json=payload)
        assert 422 == response.status_code
        assert (
            response.json()["detail"][0]["msg"]
            == "Value error, FidesKeys must only contain alphanumeric characters, '.', '_', '<', '>' or '-'. Value provided: *invalid-key"
        )

    def test_post_email_config_with_key(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        payload["key"] = "my_mailgun_messaging_config"
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])

        response = api_client.post(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        response_body = json.loads(response.text)
        email_config = db.query(MessagingConfig).filter_by(
            key="my_mailgun_messaging_config"
        )[0]

        expected_response = {
            "key": "my_mailgun_messaging_config",
            "name": "mailgun",
            "service_type": MessagingServiceType.mailgun.value,
            "details": {
                MessagingServiceDetails.API_VERSION.value: "v3",
                MessagingServiceDetails.DOMAIN.value: "my.mailgun.domain",
                MessagingServiceDetails.IS_EU_DOMAIN.value: False,
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
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.post(
            url,
            headers=auth_header,
            json={
                "key": "my_mailgun_messaging_config",
                "name": "mailgun",
                "service_type": MessagingServiceType.mailgun.value,
            },
        )
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert errors[0]["msg"] == "Value error, Messaging config must include details"

    def test_post_email_config_service_already_exists(
        self,
        api_client: TestClient,
        url,
        messaging_config,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.post(
            url,
            headers=auth_header,
            json={
                "key": "my_new_mailgun_messaging_config",
                "name": "mailgun",
                "service_type": MessagingServiceType.mailgun.value,
                "details": {MessagingServiceDetails.DOMAIN.value: "my.mailgun.domain"},
            },
        )
        assert response.status_code == 500
        assert (
            f"Key (service_type)=(mailgun) already exists" in response.json()["detail"]
        )

    def test_post_mailgun_transactional_config(
        self,
        db: Session,
        api_client: TestClient,
        payload_mailchimp_transactional,
        url,
        generate_auth_header,
    ):
        key = "mailchimp_transactional_messaging_config"
        payload_mailchimp_transactional["key"] = key
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])

        response = api_client.post(
            url,
            headers=auth_header,
            json=payload_mailchimp_transactional,
        )
        assert 200 == response.status_code

        response_body = json.loads(response.text)
        email_config = db.query(MessagingConfig).filter_by(key=key)[0]

        expected_response = {
            "key": key,
            "name": payload_mailchimp_transactional["name"],
            "service_type": MessagingServiceType.mailchimp_transactional.value,
            "details": {MessagingServiceDetails.EMAIL_FROM.value: "user@example.com"},
        }
        assert expected_response == response_body
        email_config.delete(db)

    def test_post_twilio_email_config(
        self,
        db: Session,
        api_client: TestClient,
        payload_twilio_email,
        url,
        generate_auth_header,
    ):
        payload_twilio_email["key"] = "my_twilio_email_config"
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])

        response = api_client.post(url, headers=auth_header, json=payload_twilio_email)
        assert 200 == response.status_code

        response_body = json.loads(response.text)
        email_config = db.query(MessagingConfig).filter_by(
            key="my_twilio_email_config"
        )[0]

        expected_response = {
            "key": "my_twilio_email_config",
            "name": "twilio_email",
            "service_type": MessagingServiceType.twilio_email.value,
            "details": {
                MessagingServiceDetails.TWILIO_EMAIL_FROM.value: "test@email.com"
            },
        }
        assert expected_response == response_body
        email_config.delete(db)

    def test_post_twilio_sms_config(
        self,
        db: Session,
        api_client: TestClient,
        payload_twilio_sms,
        url,
        generate_auth_header,
    ):
        payload_twilio_sms["key"] = "my_twilio_sms_config"
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])

        response = api_client.post(url, headers=auth_header, json=payload_twilio_sms)
        assert 200 == response.status_code

        response_body = json.loads(response.text)
        email_config = db.query(MessagingConfig).filter_by(key="my_twilio_sms_config")[
            0
        ]

        expected_response = {
            "key": "my_twilio_sms_config",
            "name": "twilio_sms",
            "service_type": MessagingServiceType.twilio_text.value,
            "details": None,
        }
        assert expected_response == response_body
        email_config.delete(db)

    def test_post_twilio_sms_config_lowercased(
        self,
        db: Session,
        api_client: TestClient,
        payload_twilio_sms_lowered,
        url,
        generate_auth_header,
    ):
        """
        Ensure lower-cased `service_type` values are handled well
        """

        payload_twilio_sms_lowered["key"] = "my_twilio_sms_config"
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])

        response = api_client.post(
            url, headers=auth_header, json=payload_twilio_sms_lowered
        )
        assert 200 == response.status_code

        response_body = json.loads(response.text)
        email_config = db.query(MessagingConfig).filter_by(key="my_twilio_sms_config")[
            0
        ]

        expected_response = {
            "key": "my_twilio_sms_config",
            "name": "twilio_sms",
            "service_type": MessagingServiceType.twilio_text.value,
            "details": None,
        }
        assert expected_response == response_body
        email_config.delete(db)


class TestPatchMessagingConfig:
    @pytest.fixture(scope="function")
    def url(self, messaging_config) -> str:
        return (V1_URL_PREFIX + MESSAGING_BY_KEY).format(
            config_key=messaging_config.key
        )

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            "key": "my_mailgun_messaging_config",
            "name": "mailgun new name",
            "service_type": MessagingServiceType.mailgun.value,
            "details": {MessagingServiceDetails.DOMAIN.value: "my.mailgun.domain"},
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
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_patch_email_config_with_key_not_found(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        messaging_config,
        generate_auth_header,
    ):
        url = (V1_URL_PREFIX + MESSAGING_BY_KEY).format(config_key="nonexistent_key")
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])

        response = api_client.patch(url, headers=auth_header, json=payload)
        assert response.status_code == 404
        assert response.json() == {
            "detail": "No messaging config found with key nonexistent_key"
        }

    def test_patch_email_config_with_key(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])

        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        response_body = json.loads(response.text)
        email_config = db.query(MessagingConfig).filter_by(
            key="my_mailgun_messaging_config"
        )[0]

        expected_response = {
            "key": "my_mailgun_messaging_config",
            "name": "mailgun new name",
            "service_type": MessagingServiceType.mailgun.value,
            "details": {
                MessagingServiceDetails.API_VERSION.value: "v3",
                MessagingServiceDetails.DOMAIN.value: "my.mailgun.domain",
                MessagingServiceDetails.IS_EU_DOMAIN.value: False,
            },
        }
        assert expected_response == response_body
        email_config.delete(db)


class TestPutMessagingConfigSecretsMailgun:
    @pytest.fixture(scope="function")
    def url(self, messaging_config) -> str:
        return (V1_URL_PREFIX + MESSAGING_SECRETS).format(
            config_key=messaging_config.key
        )

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            MessagingServiceSecrets.MAILGUN_API_KEY.value: "1345234524",
        }

    def test_put_config_secrets_unauthenticated(
        self, api_client: TestClient, payload, url
    ):
        response = api_client.put(url, headers={}, json=payload)
        assert 401 == response.status_code

    def test_put_config_secrets_wrong_scope(
        self, api_client: TestClient, payload, url, generate_auth_header
    ):
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_put_config_secret_invalid_config(
        self, api_client: TestClient, payload, generate_auth_header
    ):
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        url = (V1_URL_PREFIX + MESSAGING_SECRETS).format(config_key="invalid_key")
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 404 == response.status_code

    def test_update_with_invalid_secrets_key(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json={"bad_key": "12345"})

        assert response.status_code == 422
        assert response.json()["detail"] == [
            {"type": "missing", "loc": ["mailgun_api_key"], "msg": "Field required"},
            {
                "type": "extra_forbidden",
                "loc": ["bad_key"],
                "msg": "Extra inputs are not permitted",
            },
        ]

    def test_put_config_secrets(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
        messaging_config,
    ):
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        db.refresh(messaging_config)

        assert json.loads(response.text) == {
            "msg": "Secrets updated for MessagingConfig with key: my_mailgun_messaging_config.",
            "test_status": None,
            "failure_reason": None,
        }
        assert (
            messaging_config.secrets[MessagingServiceSecrets.MAILGUN_API_KEY.value]
            == "1345234524"
        )


class TestPutMessagingConfigSecretTwilioEmail:
    @pytest.fixture(scope="function")
    def url(self, messaging_config_twilio_email) -> str:
        return (V1_URL_PREFIX + MESSAGING_SECRETS).format(
            config_key=messaging_config_twilio_email.key
        )

    @pytest.fixture(scope="function")
    def payload(self):
        return {MessagingServiceSecrets.TWILIO_API_KEY.value: "23p48btcpy14b"}

    def test_put_config_secrets(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
        messaging_config_twilio_email,
    ):
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        db.refresh(messaging_config_twilio_email)

        assert json.loads(response.text) == {
            "msg": "Secrets updated for MessagingConfig with key: my_twilio_email_config.",
            "test_status": None,
            "failure_reason": None,
        }
        assert (
            messaging_config_twilio_email.secrets[
                MessagingServiceSecrets.TWILIO_API_KEY.value
            ]
            == "23p48btcpy14b"
        )


class TestPutMessagingConfigSecretMailchimpTransactional:
    @pytest.fixture(scope="function")
    def url(self, messaging_config_mailchimp_transactional) -> str:
        return (V1_URL_PREFIX + MESSAGING_SECRETS).format(
            config_key=messaging_config_mailchimp_transactional.key
        )

    def test_put_config_secrets(
        self,
        db: Session,
        api_client: TestClient,
        url,
        generate_auth_header,
        messaging_config_mailchimp_transactional,
    ):
        key = "123456789"
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.put(
            url,
            headers=auth_header,
            json={
                MessagingServiceSecrets.MAILCHIMP_TRANSACTIONAL_API_KEY.value: key,
            },
        )
        assert 200 == response.status_code

        db.refresh(messaging_config_mailchimp_transactional)

        assert json.loads(response.text) == {
            "msg": f"Secrets updated for MessagingConfig with key: {messaging_config_mailchimp_transactional.key}.",
            "test_status": None,
            "failure_reason": None,
        }
        assert (
            messaging_config_mailchimp_transactional.secrets[
                MessagingServiceSecrets.MAILCHIMP_TRANSACTIONAL_API_KEY.value
            ]
            == key
        )


class TestPutMessagingConfigSecretTwilioSms:
    @pytest.fixture(scope="function")
    def url(self, messaging_config_twilio_sms) -> str:
        return (V1_URL_PREFIX + MESSAGING_SECRETS).format(
            config_key=messaging_config_twilio_sms.key
        )

    def test_put_config_secrets_with_messaging_service_sid(
        self,
        db: Session,
        api_client: TestClient,
        url,
        generate_auth_header,
        messaging_config_twilio_sms,
    ):
        payload = {
            MessagingServiceSecrets.TWILIO_ACCOUNT_SID.value: "234ct324",
            MessagingServiceSecrets.TWILIO_AUTH_TOKEN.value: "3rcuinhewrf",
            MessagingServiceSecrets.TWILIO_MESSAGING_SERVICE_SID.value: "asdfasdf",
        }
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        db.refresh(messaging_config_twilio_sms)

        assert json.loads(response.text) == {
            "msg": "Secrets updated for MessagingConfig with key: my_twilio_sms_config.",
            "test_status": None,
            "failure_reason": None,
        }
        assert (
            messaging_config_twilio_sms.secrets[
                MessagingServiceSecrets.TWILIO_ACCOUNT_SID.value
            ]
            == "234ct324"
        )
        assert (
            messaging_config_twilio_sms.secrets[
                MessagingServiceSecrets.TWILIO_AUTH_TOKEN.value
            ]
            == "3rcuinhewrf"
        )
        assert (
            messaging_config_twilio_sms.secrets[
                MessagingServiceSecrets.TWILIO_MESSAGING_SERVICE_SID.value
            ]
            == "asdfasdf"
        )

    def test_put_config_secrets_with_sender_phone(
        self,
        db: Session,
        api_client: TestClient,
        url,
        generate_auth_header,
        messaging_config_twilio_sms,
    ):
        payload = {
            MessagingServiceSecrets.TWILIO_ACCOUNT_SID.value: "2asdf35tv5wsdf",
            MessagingServiceSecrets.TWILIO_AUTH_TOKEN.value: "23tc3",
            MessagingServiceSecrets.TWILIO_SENDER_PHONE_NUMBER.value: "+12345436543",
        }
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        db.refresh(messaging_config_twilio_sms)

        assert json.loads(response.text) == {
            "msg": "Secrets updated for MessagingConfig with key: my_twilio_sms_config.",
            "test_status": None,
            "failure_reason": None,
        }
        assert (
            messaging_config_twilio_sms.secrets[
                MessagingServiceSecrets.TWILIO_ACCOUNT_SID.value
            ]
            == "2asdf35tv5wsdf"
        )
        assert (
            messaging_config_twilio_sms.secrets[
                MessagingServiceSecrets.TWILIO_AUTH_TOKEN.value
            ]
            == "23tc3"
        )
        assert (
            messaging_config_twilio_sms.secrets[
                MessagingServiceSecrets.TWILIO_SENDER_PHONE_NUMBER.value
            ]
            == "+12345436543"
        )
        assert (
            messaging_config_twilio_sms.secrets[
                MessagingServiceSecrets.TWILIO_MESSAGING_SERVICE_SID.value
            ]
            is None
        )

    def test_put_config_secrets_with_sender_phone_incorrect_format(
        self,
        db: Session,
        api_client: TestClient,
        url,
        generate_auth_header,
        messaging_config_twilio_sms,
    ):
        payload = {
            MessagingServiceSecrets.TWILIO_ACCOUNT_SID.value: "2asdf35tv5wsdf",
            MessagingServiceSecrets.TWILIO_AUTH_TOKEN.value: "23tc3",
            MessagingServiceSecrets.TWILIO_SENDER_PHONE_NUMBER.value: "12345436543",
        }
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json=payload)

        # Because validation failed on all members, all errors were returned. This was
        # just one of them
        assert response.status_code == 422
        assert (
            f"Phone number must be formatted in E.164 format, i.e. '+15558675309'"
            in response.text
        )

    def test_put_config_secrets_with_no_sender_phone_nor_messaging_service_id(
        self,
        db: Session,
        api_client: TestClient,
        url,
        generate_auth_header,
        messaging_config_twilio_sms,
    ):
        payload = {
            MessagingServiceSecrets.TWILIO_ACCOUNT_SID.value: "2asdf35tv5wsdf",
            MessagingServiceSecrets.TWILIO_AUTH_TOKEN.value: "23tc3",
        }
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert response.status_code == 422
        assert (
            f"Either the twilio_messaging_service_sid or the twilio_sender_phone_number should be supplied"
            in response.text
        )


class TestGetMessagingConfigs:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + MESSAGING_CONFIG

    def test_get_configs_not_authenticated(self, api_client: TestClient, url) -> None:
        response = api_client.get(url)
        assert 401 == response.status_code

    def test_get_configs_wrong_scope(
        self, api_client: TestClient, url, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header([MESSAGING_DELETE])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_get_configs(
        self,
        db,
        api_client: TestClient,
        url,
        generate_auth_header,
        messaging_config,
    ):
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code

        expected_response = {
            "items": [
                {
                    "key": "my_mailgun_messaging_config",
                    "name": messaging_config.name,
                    "service_type": MessagingServiceType.mailgun.value,
                    "details": {
                        MessagingServiceDetails.API_VERSION.value: "v3",
                        MessagingServiceDetails.DOMAIN.value: "some.domain",
                        MessagingServiceDetails.IS_EU_DOMAIN.value: False,
                    },
                }
            ],
            "page": 1,
            "pages": 1,
            "size": PAGE_SIZE,
            "total": 1,
        }
        response_body = json.loads(response.text)
        assert expected_response == response_body


class TestGetMessagingConfig:
    @pytest.fixture(scope="function")
    def url(self, messaging_config) -> str:
        return (V1_URL_PREFIX + MESSAGING_BY_KEY).format(
            config_key=messaging_config.key
        )

    def test_get_config_not_authenticated(self, url, api_client: TestClient):
        response = api_client.get(url)
        assert 401 == response.status_code

    def test_get_config_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header([MESSAGING_DELETE])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_get_config_invalid(
        self, api_client: TestClient, generate_auth_header, messaging_config
    ):
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(
            (V1_URL_PREFIX + MESSAGING_BY_KEY).format(config_key="invalid"),
            headers=auth_header,
        )
        assert 404 == response.status_code

    def test_get_config(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        messaging_config,
    ):
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200

        response_body = json.loads(response.text)

        assert response_body == {
            "key": "my_mailgun_messaging_config",
            "name": messaging_config.name,
            "service_type": MessagingServiceType.mailgun.value,
            "details": {
                MessagingServiceDetails.API_VERSION.value: "v3",
                MessagingServiceDetails.DOMAIN.value: "some.domain",
                MessagingServiceDetails.IS_EU_DOMAIN.value: False,
            },
        }


class TestDeleteConfig:
    @pytest.fixture(scope="function")
    def url(self, messaging_config) -> str:
        return (V1_URL_PREFIX + MESSAGING_BY_KEY).format(
            config_key=messaging_config.key
        )

    def test_delete_config_not_authenticated(self, url, api_client: TestClient):
        response = api_client.delete(url)
        assert 401 == response.status_code

    def test_delete_config_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.delete(url, headers=auth_header)
        assert 403 == response.status_code

    def test_delete_config_invalid(self, api_client: TestClient, generate_auth_header):
        auth_header = generate_auth_header([MESSAGING_DELETE])
        response = api_client.delete(
            (V1_URL_PREFIX + MESSAGING_BY_KEY).format(config_key="invalid"),
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
        twilio_sms_config = MessagingConfig.create(
            db=db,
            data={
                "key": "my_twilio_sms_config",
                "name": "twilio_sms",
                "service_type": MessagingServiceType.twilio_text.value,
            },
        )
        url = (V1_URL_PREFIX + MESSAGING_BY_KEY).format(
            config_key=twilio_sms_config.key
        )
        auth_header = generate_auth_header([MESSAGING_DELETE])
        response = api_client.delete(url, headers=auth_header)
        assert response.status_code == 204

        db.expunge_all()
        config = db.query(MessagingConfig).filter_by(key=twilio_sms_config.key).first()
        assert config is None


class TestGetDefaultMessagingConfig:
    @pytest.fixture(scope="function")
    def url(self, messaging_config: MessagingConfig) -> str:
        return (V1_URL_PREFIX + MESSAGING_DEFAULT_BY_TYPE).format(
            service_type=messaging_config.service_type.value
        )

    @pytest.fixture(scope="function")
    def url_uppercase(self, messaging_config: MessagingConfig) -> str:
        return (V1_URL_PREFIX + MESSAGING_DEFAULT_BY_TYPE).format(
            service_type=messaging_config.service_type.value.upper()
        )

    def test_get_default_config_not_authenticated(self, url, api_client: TestClient):
        response = api_client.get(url)
        assert 401 == response.status_code

    def test_get_default_config_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header([MESSAGING_DELETE])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_get_default_config_invalid(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(
            (V1_URL_PREFIX + MESSAGING_DEFAULT_BY_TYPE).format(service_type="invalid"),
            headers=auth_header,
        )
        assert 422 == response.status_code

    def test_get_default_config_not_exist(
        self,
        api_client: TestClient,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(
            (V1_URL_PREFIX + MESSAGING_DEFAULT_BY_TYPE).format(
                service_type=MessagingServiceType.mailgun.value
            ),
            headers=auth_header,
        )
        assert 404 == response.status_code

    def test_get_default_config(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        messaging_config: MessagingConfig,
    ):
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200

        response_body = response.json()

        assert response_body == {
            "key": "my_mailgun_messaging_config",
            "name": messaging_config.name,
            "service_type": MessagingServiceType.mailgun.value,
            "details": {
                MessagingServiceDetails.API_VERSION.value: "v3",
                MessagingServiceDetails.DOMAIN.value: "some.domain",
                MessagingServiceDetails.IS_EU_DOMAIN.value: False,
            },
        }

    def test_get_default_config_uppered_url(
        self,
        url_uppercase,
        api_client: TestClient,
        generate_auth_header,
        messaging_config: MessagingConfig,
    ):
        """
        Ensure that a uppercased URL can be used, since by default we're
        using the lowercased enum values in our URL
        """
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(url_uppercase.lower(), headers=auth_header)
        assert response.status_code == 200

        response_body = response.json()

        assert response_body == {
            "key": "my_mailgun_messaging_config",
            "name": messaging_config.name,
            "service_type": MessagingServiceType.mailgun.value,
            "details": {
                MessagingServiceDetails.API_VERSION.value: "v3",
                MessagingServiceDetails.DOMAIN.value: "some.domain",
                MessagingServiceDetails.IS_EU_DOMAIN.value: False,
            },
        }


class TestPutDefaultMessagingConfig:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + MESSAGING_DEFAULT

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            "service_type": MessagingServiceType.mailgun.value,
            "details": {MessagingServiceDetails.DOMAIN.value: "my.mailgun.domain"},
        }

    def test_put_default_messaging_config_not_authenticated(
        self,
        api_client: TestClient,
        payload,
        url,
    ):
        response = api_client.put(url, headers={}, json=payload)
        assert 401 == response.status_code

    def test_put_default_messaging_config_incorrect_scope(
        self,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_put_default_messaging(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json=payload)

        assert 200 == response.status_code
        response_body = json.loads(response.text)

        assert response_body["key"] is not None
        assert response_body["service_type"] == payload["service_type"]
        assert response_body["details"]["domain"] == payload["details"]["domain"]
        messaging_configs = (
            db.query(MessagingConfig)
            .filter_by(service_type=payload["service_type"])
            .all()
        )
        assert len(messaging_configs) == 1
        assert messaging_configs[0].key == response_body["key"]
        assert messaging_configs[0].service_type.value == payload["service_type"]
        assert messaging_configs[0].details["domain"] == payload["details"]["domain"]

        messaging_configs[0].delete(db)

    def test_put_messaging_default_config_with_key_rejected(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        payload["key"] = "my_messaging_config_key"
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])

        response = api_client.put(url, headers=auth_header, json=payload)
        assert 422 == response.status_code

    def test_put_messaging_default_config_with_name_rejected(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        payload["name"] = "my_messaging_config_name"
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])

        response = api_client.put(url, headers=auth_header, json=payload)
        assert 422 == response.status_code

    @pytest.mark.parametrize(
        "service_type, details",
        [
            (
                MessagingServiceType.twilio_email.value,
                {"twilio_email_from": "test_email@test.com"},
            ),
            (
                MessagingServiceType.twilio_email.value.lower(),
                {"twilio_email_from": "test_email@test.com"},
            ),
            (MessagingServiceType.twilio_text.value, None),
        ],
    )
    def test_put_default_messaging_config_with_different_service_types(
        self,
        db: Session,
        api_client: TestClient,
        service_type,
        details,
        url,
        generate_auth_header,
    ):
        payload = {"service_type": service_type}
        if details:
            payload["details"] = details
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json=payload)

        assert 200 == response.status_code
        response_body = json.loads(response.text)
        config_key = response_body["key"]
        messaging_config = MessagingConfig.get_by(db, field="key", value=config_key)
        assert service_type == response_body["service_type"]
        assert service_type == messaging_config.service_type.value
        messaging_config.delete(db)

    def test_put_default_messaging_config_twice_only_one_record(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])

        # try an initial put, assert it works well
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code
        response_body = json.loads(response.text)
        config_key = response_body["key"]
        messaging_configs = (
            db.query(MessagingConfig)
            .filter_by(service_type=payload["service_type"])
            .all()
        )
        assert len(messaging_configs) == 1
        messaging_config = messaging_configs[0]
        assert messaging_config.key == config_key
        assert messaging_config.details["domain"] == payload["details"]["domain"]

        # try a follow-up put after changing a detail assert it made the update to existing record
        payload["details"][MessagingServiceDetails.DOMAIN.value] = "a.new.domain"
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code
        response_body = json.loads(response.text)
        assert config_key == response_body["key"]
        messaging_configs = (
            db.query(MessagingConfig)
            .filter_by(service_type=payload["service_type"])
            .all()
        )
        assert len(messaging_configs) == 1
        messaging_config = messaging_configs[0]
        db.refresh(messaging_config)
        assert messaging_config.key == config_key
        assert (
            messaging_config.details[MessagingServiceDetails.DOMAIN.value]
            == "a.new.domain"
        )

        messaging_config.delete(db)

    def test_put_default_config_invalid_details(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        payload,
    ):
        payload["details"] = {"invalid": "invalid"}

        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])

        response = api_client.put(url, headers=auth_header, json=payload)
        assert response.status_code == 422

    def test_put_default_config_invalid_details_for_type(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        payload,
    ):
        # add a twilio detail field to a mailgun request, should receive a validation error
        payload["details"] = {"twilio_email_from": "invalid"}

        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])

        response = api_client.put(url, headers=auth_header, json=payload)
        assert response.status_code == 422


class TestPutDefaultMessagingConfigSecrets:
    @pytest.fixture(scope="function")
    def url(self, messaging_config) -> str:
        return (V1_URL_PREFIX + MESSAGING_DEFAULT_SECRETS).format(
            service_type=MessagingServiceType.mailgun.value
        )

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            MessagingServiceSecrets.MAILGUN_API_KEY.value: "1345234524",
        }

    def test_put_default_messaging_secrets_unauthenticated(
        self, api_client: TestClient, payload, url
    ):
        response = api_client.put(url, headers={}, json=payload)
        assert 401 == response.status_code

    def test_put_default_messaging_secrets_wrong_scope(
        self, api_client: TestClient, payload, url, generate_auth_header
    ):
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_put_default_messaging_secret_invalid_config(
        self, api_client: TestClient, payload, generate_auth_header
    ):
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        url = (V1_URL_PREFIX + MESSAGING_DEFAULT_SECRETS).format(
            service_type="invalid_type"
        )
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 422 == response.status_code

    def test_put_default_messaging_secret_missing_config(
        self, api_client: TestClient, payload, generate_auth_header
    ):
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        url = (V1_URL_PREFIX + MESSAGING_DEFAULT_SECRETS).format(
            service_type=MessagingServiceType.mailgun.value
        )
        # this should get a 404 because we have not added the messaging config
        # through a fixture
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 404 == response.status_code

    def test_update_default_with_invalid_secrets_key(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json={"bad_key": "12345"})
        assert response.status_code == 422
        assert "Field required" in response.text
        assert "Extra inputs are not permitted" in response.text

    @mock.patch("fides.api.models.messaging.MessagingConfig.set_secrets")
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
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert response.status_code == 400

    def test_put_default_config_secrets(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
        messaging_config,
    ):
        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        db.refresh(messaging_config)

        assert json.loads(response.text) == {
            "msg": f"Secrets updated for MessagingConfig with key: {messaging_config.key}.",
            "test_status": None,
            "failure_reason": None,
        }
        assert messaging_config.secrets == payload

    def test_put_default_config_secrets_lowered(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
        messaging_config,
    ):
        """
        Ensure that a lowercased URL can be used, since by default we're
        using the uppercased enum values in our URL
        """

        auth_header = generate_auth_header([MESSAGING_CREATE_OR_UPDATE])
        response = api_client.put(url.lower(), headers=auth_header, json=payload)
        assert 200 == response.status_code

        db.refresh(messaging_config)

        assert json.loads(response.text) == {
            "msg": f"Secrets updated for MessagingConfig with key: {messaging_config.key}.",
            "test_status": None,
            "failure_reason": None,
        }
        assert messaging_config.secrets == payload


class TestGetActiveDefaultMessagingConfig:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + MESSAGING_ACTIVE_DEFAULT

    def test_get_active_default_config_not_authenticated(
        self, url, api_client: TestClient
    ):
        response = api_client.get(url)
        assert 401 == response.status_code

    def test_get_active_default_config_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header([MESSAGING_DELETE])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_get_active_default_none_set(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 404 == response.status_code

    @pytest.mark.usefixtures("notification_service_type_none")
    def test_get_active_default_app_setting_not_set(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        messaging_config,
    ):
        """
        Even with `messaing_config` fixture creating a default messaging config,
        we should still not get an active default config if the
        `notifications.notification_service_type` config property has not been set

        """
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 404 == response.status_code

    @pytest.fixture(scope="function")
    def notification_service_type_mailgun(self, db):
        """Set mailgun as the `notification_service_type` property"""
        original_value = CONFIG.notifications.notification_service_type
        CONFIG.notifications.notification_service_type = "mailgun"
        ApplicationConfig.update_config_set(db, CONFIG)
        yield
        CONFIG.notifications.notification_service_type = original_value
        ApplicationConfig.update_config_set(db, CONFIG)

    @pytest.fixture(scope="function")
    def notification_service_type_none(self, db):
        """Set the `notification_service_type` property to `None`"""
        original_value = CONFIG.notifications.notification_service_type
        CONFIG.notifications.notification_service_type = None
        ApplicationConfig.update_config_set(db, CONFIG)
        yield
        CONFIG.notifications.notification_service_type = original_value
        ApplicationConfig.update_config_set(db, CONFIG)

    @pytest.fixture(scope="function")
    def notification_service_type_invalid(self, db):
        """Set an invalid string as the `notification_service_type` property"""
        original_value = CONFIG.notifications.notification_service_type
        CONFIG.notifications.notification_service_type = "invalid_service_type"
        ApplicationConfig.update_config_set(db, CONFIG)
        yield
        CONFIG.notifications.notification_service_type = original_value
        ApplicationConfig.update_config_set(db, CONFIG)

    @pytest.mark.usefixtures("notification_service_type_mailgun")
    def test_get_active_default_app_setting_but_not_configured(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        """
        Without `messaging_config` fixture creating a default messaging config,
        but by setting the application setting for "notification_service_type" to mailgun,
        we should get a 404, since we have no mailgun default configured.
        """
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 404 == response.status_code

    @pytest.mark.usefixtures("notification_service_type_invalid")
    def test_get_active_default_app_setting_invalid(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        loguru_caplog,
    ):
        """
        This is contrived and should not be able to occur, but here we test what happens
        if somehow the `notifications.notification_service_type` config property is set
        to an invalid value.
        """

        error_message = "Unknown notification_service_type"
        response_error = "Invalid notification_service_type configured."
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )

        assert response.status_code == 400
        assert response.json().get("detail") == response_error

    @pytest.mark.usefixtures("notification_service_type_mailgun")
    def test_get_active_default_config(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        messaging_config: MessagingConfig,
    ):
        """
        We should get back our mailgun config default now that
        we set mailgun as the notification_service_type via app setting
        """
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200

        response_body = response.json()

        assert response_body == {
            "key": "my_mailgun_messaging_config",
            "name": messaging_config.name,
            "service_type": MessagingServiceType.mailgun.value,
            "details": {
                MessagingServiceDetails.API_VERSION.value: "v3",
                MessagingServiceDetails.DOMAIN.value: "some.domain",
                MessagingServiceDetails.IS_EU_DOMAIN.value: False,
            },
        }


class TestGetMessagingStatus:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + MESSAGING_STATUS

    def test_get_messaging_status_not_authenticated(self, url, api_client: TestClient):
        response = api_client.get(url)
        assert 401 == response.status_code

    def test_get_messaging_status_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header([MESSAGING_DELETE])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_get_messaging_status_none_set(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        response = MessagingConfigStatusMessage(**response.json())
        assert response.config_status == MessagingConfigStatus.not_configured
        assert response.detail == "No active default messaging configuration found"

    @pytest.mark.usefixtures("notification_service_type_none")
    def test_get_messaging_status_app_setting_not_set(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        messaging_config,
    ):
        """
        Even with `messaing_config` fixture creating a default messaging config,
        we should still not get a successful status reading, since the
        `notifications.notification_service_type` config property has not been set

        """
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        response = MessagingConfigStatusMessage(**response.json())
        assert response.config_status == MessagingConfigStatus.not_configured
        assert response.detail == "No active default messaging configuration found"

    @pytest.fixture(scope="function")
    def notification_service_type_mailgun(self, db):
        """Set mailgun as the `notification_service_type` property"""
        original_value = CONFIG.notifications.notification_service_type
        CONFIG.notifications.notification_service_type = (
            MessagingServiceType.mailgun.value
        )
        ApplicationConfig.update_config_set(db, CONFIG)
        yield
        CONFIG.notifications.notification_service_type = original_value
        ApplicationConfig.update_config_set(db, CONFIG)

    @pytest.fixture(scope="function")
    def notification_service_type_twilio_text(self, db):
        """Set twilio_text as the `notification_service_type` property"""
        original_value = CONFIG.notifications.notification_service_type
        CONFIG.notifications.notification_service_type = (
            MessagingServiceType.twilio_text.value
        )
        ApplicationConfig.update_config_set(db, CONFIG)
        yield
        CONFIG.notifications.notification_service_type = original_value
        ApplicationConfig.update_config_set(db, CONFIG)

    @pytest.fixture(scope="function")
    def notification_service_type_twilio_email(self, db):
        """Set twilio_email as the `notification_service_type` property"""
        original_value = CONFIG.notifications.notification_service_type
        CONFIG.notifications.notification_service_type = (
            MessagingServiceType.twilio_email.value
        )
        ApplicationConfig.update_config_set(db, CONFIG)
        yield
        CONFIG.notifications.notification_service_type = original_value
        ApplicationConfig.update_config_set(db, CONFIG)

    @pytest.fixture(scope="function")
    def notification_service_type_none(self, db):
        """Set the `notification_service_type` property to `None`"""
        original_value = CONFIG.notifications.notification_service_type
        CONFIG.notifications.notification_service_type = None
        ApplicationConfig.update_config_set(db, CONFIG)
        yield
        CONFIG.notifications.notification_service_type = original_value
        ApplicationConfig.update_config_set(db, CONFIG)

    @pytest.mark.usefixtures("notification_service_type_twilio_text")
    def test_get_messaging_status_app_setting_wrong_value(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        messaging_config,
    ):
        """
        Even with `messaing_config` fixture creating a default messaging config,
        we should still not get a successful status reading, since the
        `notifications.notification_service_type` config property has been set to
        a service type that is not mailgun

        """
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        response = MessagingConfigStatusMessage(**response.json())
        assert response.config_status == MessagingConfigStatus.not_configured
        assert response.detail == "No active default messaging configuration found"

    @pytest.mark.usefixtures("notification_service_type_mailgun")
    def test_get_messaging_status_app_setting_but_not_configured(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        """
        Without `messaging_config` fixture creating a default messaging config,
        but by setting the application setting for "notification_service_type" to mailgun,
        we should get a failure, since we have no mailgun default configured.
        """
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        response = MessagingConfigStatusMessage(**response.json())
        assert response.config_status == MessagingConfigStatus.not_configured
        assert response.detail == "No active default messaging configuration found"

    @pytest.mark.usefixtures("notification_service_type_mailgun", "messaging_config")
    def test_get_messaging_status_secrets_not_present(
        self,
        url,
        db: Session,
        api_client: TestClient,
        generate_auth_header,
    ):
        """
        If secrets aren't present on the mailgun config, we should get a failure
        """
        messaging_config = db.query(MessagingConfig).first()
        messaging_config.secrets = {}
        messaging_config.save(db)

        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        response = MessagingConfigStatusMessage(**response.json())
        assert response.config_status == MessagingConfigStatus.not_configured
        assert "No secrets found" in response.detail

    @pytest.mark.usefixtures("notification_service_type_mailgun", "messaging_config")
    def test_get_messaging_status_wrong_secrets(
        self,
        url,
        db: Session,
        api_client: TestClient,
        generate_auth_header,
    ):
        """
        If non-mailgun secrets are somehow on the mailgun config, we should get a failure
        """
        messaging_config = db.query(MessagingConfig).first()
        messaging_config.secrets = {
            MessagingServiceSecrets.TWILIO_ACCOUNT_SID.value: "some_sid"
        }
        messaging_config.save(db)

        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        response = MessagingConfigStatusMessage(**response.json())
        assert response.config_status == MessagingConfigStatus.not_configured
        assert "Invalid secrets found" in response.detail

    @pytest.mark.usefixtures("notification_service_type_mailgun", "messaging_config")
    def test_get_messaging_status_details_not_present(
        self,
        url,
        db: Session,
        api_client: TestClient,
        generate_auth_header,
    ):
        """
        If details aren't present on the mailgun config, we should get a failure
        """
        messaging_config = db.query(MessagingConfig).first()
        messaging_config.details = {}
        messaging_config.save(db)

        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        response = MessagingConfigStatusMessage(**response.json())
        assert response.config_status == MessagingConfigStatus.not_configured
        assert "Invalid or unpopulated details" in response.detail

    @pytest.mark.usefixtures(
        "notification_service_type_twilio_email", "messaging_config_twilio_email"
    )
    def test_get_messaging_status_details_not_present_twilio_email(
        self,
        url,
        db: Session,
        api_client: TestClient,
        generate_auth_header,
    ):
        """
        If details aren't present on the twilio_email config, we should get a failure
        """
        messaging_config = db.query(MessagingConfig).first()
        messaging_config.details = {}
        messaging_config.save(db)

        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        response = MessagingConfigStatusMessage(**response.json())
        assert response.config_status == MessagingConfigStatus.not_configured
        assert "Invalid or unpopulated details" in response.detail

    @pytest.mark.usefixtures("notification_service_type_mailgun", "messaging_config")
    def test_get_messaging_status_details_wrong_values(
        self,
        url,
        db: Session,
        api_client: TestClient,
        generate_auth_header,
    ):
        """
        If twilio_email details are on the mailgun config, we should get a failure
        """
        messaging_config = db.query(MessagingConfig).first()
        messaging_config.details = {
            MessagingServiceDetails.TWILIO_EMAIL_FROM.value: "some_sample_email"
        }
        messaging_config.save(db)

        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        response = MessagingConfigStatusMessage(**response.json())
        assert response.config_status == MessagingConfigStatus.not_configured
        assert "Invalid or unpopulated details" in response.detail

    @pytest.mark.usefixtures("notification_service_type_mailgun", "messaging_config")
    def test_get_messaging_status(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        """
        We should get back a successful response now that
        we set mailgun as the notification_service_type via app setting
        and the config has been added via fixture
        """
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        response = MessagingConfigStatusMessage(**response.json())
        assert response.config_status == MessagingConfigStatus.configured
        assert MessagingServiceType.mailgun.value in (response.detail)

    @pytest.mark.usefixtures(
        "notification_service_type_twilio_text", "messaging_config_twilio_sms"
    )
    def test_get_messaging_status_twilio_text(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        """
        We should get back a successful response now that
        we set mailgun as the notification_service_type via app setting
        and the config has been added via fixture
        """
        auth_header = generate_auth_header([MESSAGING_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        response = MessagingConfigStatusMessage(**response.json())
        assert response.config_status == MessagingConfigStatus.configured
        assert MessagingServiceType.twilio_text.value in (response.detail)


class TestTestMessage:
    @pytest.fixture
    def url(self):
        return f"{V1_URL_PREFIX}{MESSAGING_TEST_DEPRECATED}"

    @pytest.mark.parametrize(
        "info",
        [{"phone_number": "+19198675309"}, {"email": "some@email.com"}],
    )
    @patch("fides.api.api.v1.endpoints.messaging_endpoints.dispatch_message")
    def test_test_message(
        self, mock_dispatch_message, info, generate_auth_header, url, api_client
    ):
        auth_header = generate_auth_header(scopes=[MESSAGING_CREATE_OR_UPDATE])
        response = api_client.post(url, json=info, headers=auth_header)
        assert response.status_code == 200
        assert mock_dispatch_message.called

    def test_test_message_unauthorized(self, url, api_client):
        response = api_client.post(url, json={"phone_number": "+19198675309"})
        assert response.status_code == 401

    @pytest.mark.parametrize(
        "info",
        [
            {"phone_number": "+19198675309", "email": "some@email.com"},
            {"phone_number": None, "email": None},
        ],
    )
    def test_test_message_invalid(self, info, generate_auth_header, url, api_client):
        auth_header = generate_auth_header(scopes=[MESSAGING_CREATE_OR_UPDATE])
        response = api_client.post(
            url,
            json=info,
            headers=auth_header,
        )
        assert response.status_code == 400

    @patch(
        "fides.api.api.v1.endpoints.messaging_endpoints.dispatch_message",
        side_effect=MessageDispatchException("No service"),
    )
    def test_test_message_dispatch_error(
        self, mock_dispatch_message, generate_auth_header, url, api_client
    ):
        auth_header = generate_auth_header(scopes=[MESSAGING_CREATE_OR_UPDATE])
        response = api_client.post(
            url, json={"phone_number": "+19198675309"}, headers=auth_header
        )
        assert response.status_code == 400
        assert mock_dispatch_message.called


class TestGetBasicMessagingTemplates:
    @pytest.fixture
    def url(self) -> str:
        return V1_URL_PREFIX + BASIC_MESSAGING_TEMPLATES

    def test_get_messaging_templates_unauthorized(
        self, url, api_client: TestClient, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 403

    def test_get_messaging_templates_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[MESSAGING_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 403

    def test_get_messaging_templates(
        self, url, api_client: TestClient, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[MESSAGING_TEMPLATE_UPDATE])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200

        # Validate the response conforms to the expected model
        [BasicMessagingTemplateResponse(**item) for item in response.json()]


class TestPutBasicMessagingTemplates:
    @pytest.fixture
    def url(self) -> str:
        return V1_URL_PREFIX + BASIC_MESSAGING_TEMPLATES

    @pytest.fixture
    def payload(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "subject_identity_verification",
                "content": {
                    "body": "Your privacy request verification code is __CODE__. Please return to the Privacy Center and enter the code to continue. You have __MINUTES__ minutes.",
                    "subject": "Your code is __CODE__",
                },
            },
        ]

    def test_put_messaging_templates_unauthorized(
        self, url, api_client: TestClient, generate_auth_header, payload
    ) -> None:
        auth_header = generate_auth_header(scopes=[])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert response.status_code == 403

    def test_put_messaging_templates_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header, payload
    ) -> None:
        auth_header = generate_auth_header(scopes=[MESSAGING_READ])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert response.status_code == 403

    def test_put_messaging_templates(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        payload,
    ) -> None:
        auth_header = generate_auth_header(scopes=[MESSAGING_TEMPLATE_UPDATE])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert response.status_code == 200
        assert response.json() == {
            "succeeded": [
                {
                    "type": "subject_identity_verification",
                    "content": {
                        "body": "Your privacy request verification code is __CODE__. Please return to the Privacy Center and enter the code to continue. You have __MINUTES__ minutes.",
                        "subject": "Your code is __CODE__",
                    },
                    "label": "Subject identity verification",
                }
            ],
            "failed": [],
        }

    def test_put_messaging_templates_missing_values(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        """Verify templates with empty subject/body values are reverted to their default values."""
        auth_header = generate_auth_header(scopes=[MESSAGING_TEMPLATE_UPDATE])
        response = api_client.put(
            url,
            headers=auth_header,
            json=[
                {
                    "type": "subject_identity_verification",
                    "content": {
                        "body": None,
                        "subject": None,
                    },
                },
            ],
        )
        assert response.status_code == 200
        assert response.json() == {
            "succeeded": [
                {
                    "type": "subject_identity_verification",
                    "content": {
                        "body": "Your privacy request verification code is __CODE__. Please return to the Privacy Center and enter the code to continue. This code will expire in __MINUTES__ minutes.",
                        "subject": "Your one-time code is __CODE__",
                    },
                    "label": "Subject identity verification",
                }
            ],
            "failed": [],
        }

    def test_put_messaging_templates_invalid_type(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[MESSAGING_TEMPLATE_UPDATE])
        response = api_client.put(
            url,
            headers=auth_header,
            json=[
                {
                    "type": "invalid_type",
                    "content": {
                        "body": None,
                        "subject": None,
                    },
                },
            ],
        )
        assert response.status_code == 200
        assert response.json() == {
            "succeeded": [],
            "failed": [
                {
                    "message": "Invalid template type.",
                    "data": {
                        "type": "invalid_type",
                        "content": {"body": None, "subject": None},
                    },
                }
            ],
        }


class TestGetMessagingTemplateDefaultByTemplateType:
    @pytest.fixture
    def url(self) -> str:
        return (V1_URL_PREFIX + MESSAGING_TEMPLATE_DEFAULT_BY_TEMPLATE_TYPE).format(
            template_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        )

    def test_get_messaging_template_default_unauthorized(
        self, url, api_client: TestClient, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 403

    def test_get_messaging_template_default_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[MESSAGING_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 403

    def test_get_messaging_template_default_unsupported(
        self, api_client: TestClient, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[MESSAGING_TEMPLATE_UPDATE])
        # This template type is not supported for having defaults
        url = (V1_URL_PREFIX + MESSAGING_TEMPLATE_DEFAULT_BY_TEMPLATE_TYPE).format(
            template_type=MessagingActionType.CONSENT_REQUEST_EMAIL_FULFILLMENT.value
        )
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 400

    def test_get_messaging_template_default(
        self, url, api_client: TestClient, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[MESSAGING_TEMPLATE_UPDATE])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        resp = response.json()

        # Validate the response conforms to the expected model
        MessagingTemplateDefault(**resp)


class TestGetMessagingTemplateById:
    @pytest.fixture
    def url(self, messaging_template_subject_identity_verification) -> str:
        return (V1_URL_PREFIX + MESSAGING_TEMPLATE_BY_ID).format(
            template_id=messaging_template_subject_identity_verification.id
        )

    def test_get_messaging_template_by_id_unauthorized(
        self, url, api_client: TestClient, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 403

    def test_get_messaging_template_by_id_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[MESSAGING_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 403

    def test_get_messaging_template_by_id_invalid_id(
        self, api_client: TestClient, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[MESSAGING_TEMPLATE_UPDATE])
        url = (V1_URL_PREFIX + MESSAGING_TEMPLATE_BY_ID).format(template_id="invalid")
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 404

    def test_get_messaging_template_by_id_success(
        self,
        url,
        db: Session,
        api_client: TestClient,
        generate_auth_header,
        property_a,
        messaging_template_subject_identity_verification,
    ) -> None:
        auth_header = generate_auth_header(scopes=[MESSAGING_TEMPLATE_UPDATE])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        template = response.json()
        assert len(template["properties"]) == 1
        assert template["properties"][0]["id"] == property_a.id
        assert template["is_enabled"] is True


class TestDeleteMessagingTemplateById:
    @pytest.fixture
    def url(self, messaging_template_subject_identity_verification) -> str:
        return (V1_URL_PREFIX + MESSAGING_TEMPLATE_BY_ID).format(
            template_id=messaging_template_subject_identity_verification.id
        )

    def test_delete_messaging_template_by_id_unauthorized(
        self, url, api_client: TestClient, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[])
        response = api_client.delete(url, headers=auth_header)
        assert response.status_code == 403

    def test_delete_messaging_template_by_id_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[MESSAGING_READ])
        response = api_client.delete(url, headers=auth_header)
        assert response.status_code == 403

    def test_delete_messaging_template_by_id_invalid_id(
        self, api_client: TestClient, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[MESSAGING_TEMPLATE_UPDATE])
        url = (V1_URL_PREFIX + MESSAGING_TEMPLATE_BY_ID).format(template_id="invalid")
        response = api_client.delete(url, headers=auth_header)
        assert response.status_code == 404

    def test_delete_messaging_template_by_id__validation_error(
        self,
        url,
        db: Session,
        api_client: TestClient,
        generate_auth_header,
        messaging_template_subject_identity_verification,
    ) -> None:
        auth_header = generate_auth_header(scopes=[MESSAGING_TEMPLATE_UPDATE])
        response = api_client.delete(url, headers=auth_header)
        assert response.status_code == 400

    def test_delete_messaging_template_by_id_success(
        self,
        db: Session,
        api_client: TestClient,
        generate_auth_header,
        messaging_template_no_property,
        property_a,
    ) -> None:
        # Creating new config, so we don't run into issues trying to clean up a deleted fixture
        template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        content = {
            "subject": "Here is your code __CODE__",
            "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
        }
        data = {
            "content": content,
            "properties": [{"id": property_a.id, "name": property_a.name}],
            "is_enabled": True,
            "type": template_type,
        }
        messaging_template = MessagingTemplate.create(
            db=db,
            data=data,
        )

        url = (V1_URL_PREFIX + MESSAGING_TEMPLATE_BY_ID).format(
            template_id=messaging_template.id
        )
        auth_header = generate_auth_header(scopes=[MESSAGING_TEMPLATE_UPDATE])
        response = api_client.delete(url, headers=auth_header)
        assert response.status_code == 204

        db.expunge_all()
        template = (
            db.query(MessagingTemplate).filter_by(id=messaging_template.id).first()
        )
        assert template is None
