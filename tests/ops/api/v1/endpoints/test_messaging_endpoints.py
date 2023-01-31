import json

import pytest
from fastapi_pagination import Params

from fides.api.ops.api.v1.scope_registry import (
    MESSAGING_CREATE_OR_UPDATE,
    MESSAGING_DELETE,
    MESSAGING_READ,
)
from fides.api.ops.api.v1.urn_registry import (
    MESSAGING_BY_KEY,
    MESSAGING_CONFIG,
    MESSAGING_SECRETS,
    V1_URL_PREFIX,
)
from fides.api.ops.models.messaging import MessagingConfig
from fides.api.ops.schemas.messaging.messaging import (
    MessagingServiceDetails,
    MessagingServiceSecrets,
    MessagingServiceType,
)

PAGE_SIZE = Params().size


class TestPostMessagingConfig:
    @pytest.fixture(scope="function")
    def url(self):
        return V1_URL_PREFIX + MESSAGING_CONFIG

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            "name": "mailgun",
            "service_type": MessagingServiceType.MAILGUN.value,
            "details": {MessagingServiceDetails.DOMAIN.value: "my.mailgun.domain"},
        }

    @pytest.fixture(scope="function")
    def payload_twilio_email(self):
        return {
            "name": "twilio_email",
            "service_type": MessagingServiceType.TWILIO_EMAIL.value,
            "details": {
                MessagingServiceDetails.TWILIO_EMAIL_FROM.value: "test@email.com"
            },
        }

    @pytest.fixture(scope="function")
    def payload_twilio_sms(self):
        return {
            "name": "twilio_sms",
            "service_type": MessagingServiceType.TWILIO_TEXT.value,
        }

    def test_post_email_config_not_authenticated(self, api_client, payload, url):
        response = api_client.post(url, headers={}, json=payload)
        assert 401 == response.status_code

    @pytest.mark.parametrize("auth_header", [[MESSAGING_READ]], indirect=True)
    def test_post_email_config_incorrect_scope(
        self, auth_header, api_client, payload, url
    ):
        response = api_client.post(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    @pytest.mark.parametrize(
        "auth_header", [[MESSAGING_CREATE_OR_UPDATE]], indirect=True
    )
    def test_post_email_config_with_invalid_mailgun_details(
        self,
        auth_header,
        api_client,
        url,
        payload,
    ):
        payload["details"] = {"invalid": "invalid"}

        response = api_client.post(url, headers=auth_header, json=payload)
        assert 422 == response.status_code
        assert response.json()["detail"][0]["msg"] == "field required"
        assert response.json()["detail"][1]["msg"] == "extra fields not permitted"

    @pytest.mark.parametrize(
        "auth_header", [[MESSAGING_CREATE_OR_UPDATE]], indirect=True
    )
    def test_post_email_config_with_not_supported_service_type(
        self,
        auth_header,
        api_client,
        url,
        payload,
    ):
        payload["service_type"] = "twilio"
        response = api_client.post(url, headers=auth_header, json=payload)
        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "value is not a valid enumeration member; permitted: 'MAILGUN', 'TWILIO_TEXT', 'TWILIO_EMAIL'"
        )

    @pytest.mark.parametrize(
        "auth_header", [[MESSAGING_CREATE_OR_UPDATE]], indirect=True
    )
    def test_post_email_config_with_no_key(self, auth_header, api_client, payload, url):
        response = api_client.post(url, headers=auth_header, json=payload)

        assert 200 == response.status_code
        response_body = json.loads(response.text)

        assert response_body["key"] == "mailgun"

    @pytest.mark.parametrize(
        "auth_header", [[MESSAGING_CREATE_OR_UPDATE]], indirect=True
    )
    def test_post_email_config_with_invalid_key(
        self, auth_header, api_client, payload, url
    ):
        payload["key"] = "*invalid-key"
        response = api_client.post(url, headers=auth_header, json=payload)
        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "FidesKeys must only contain alphanumeric characters, '.', '_', '<', '>' or '-'. Value provided: *invalid-key"
        )

    @pytest.mark.parametrize(
        "auth_header", [[MESSAGING_CREATE_OR_UPDATE]], indirect=True
    )
    def test_post_email_config_with_key(self, auth_header, api_client, payload, url):
        payload["key"] = "my_mailgun_messaging_config"

        response = api_client.post(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        response_body = json.loads(response.text)

        expected_response = {
            "key": "my_mailgun_messaging_config",
            "name": "mailgun",
            "service_type": MessagingServiceType.MAILGUN.value,
            "details": {
                MessagingServiceDetails.API_VERSION.value: "v3",
                MessagingServiceDetails.DOMAIN.value: "my.mailgun.domain",
                MessagingServiceDetails.IS_EU_DOMAIN.value: False,
            },
        }
        assert expected_response == response_body

    @pytest.mark.parametrize(
        "auth_header", [[MESSAGING_CREATE_OR_UPDATE]], indirect=True
    )
    def test_post_email_config_missing_detail(self, auth_header, api_client, url):
        response = api_client.post(
            url,
            headers=auth_header,
            json={
                "key": "my_mailgun_messaging_config",
                "name": "mailgun",
                "service_type": MessagingServiceType.MAILGUN.value,
            },
        )
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert errors[0]["msg"] == "Messaging config must include details"

    @pytest.mark.usefixtures("messaging_config")
    @pytest.mark.parametrize(
        "auth_header", [[MESSAGING_CREATE_OR_UPDATE]], indirect=True
    )
    def test_post_email_config_service_already_exists(
        self, auth_header, api_client, url
    ):
        response = api_client.post(
            url,
            headers=auth_header,
            json={
                "key": "my_new_mailgun_messaging_config",
                "name": "mailgun",
                "service_type": MessagingServiceType.MAILGUN.value,
                "details": {MessagingServiceDetails.DOMAIN.value: "my.mailgun.domain"},
            },
        )
        assert response.status_code == 500
        assert (
            f"Key (service_type)=(MAILGUN) already exists" in response.json()["detail"]
        )

    @pytest.mark.parametrize(
        "auth_header", [[MESSAGING_CREATE_OR_UPDATE]], indirect=True
    )
    def test_post_twilio_email_config(
        self, auth_header, api_client, payload_twilio_email, url
    ):
        payload_twilio_email["key"] = "my_twilio_email_config"

        response = api_client.post(url, headers=auth_header, json=payload_twilio_email)
        assert 200 == response.status_code

        response_body = json.loads(response.text)

        expected_response = {
            "key": "my_twilio_email_config",
            "name": "twilio_email",
            "service_type": MessagingServiceType.TWILIO_EMAIL.value,
            "details": {
                MessagingServiceDetails.TWILIO_EMAIL_FROM.value: "test@email.com"
            },
        }
        assert expected_response == response_body

    @pytest.mark.parametrize(
        "auth_header", [[MESSAGING_CREATE_OR_UPDATE]], indirect=True
    )
    def test_post_twilio_sms_config(
        self, auth_header, api_client, payload_twilio_sms, url
    ):
        payload_twilio_sms["key"] = "my_twilio_sms_config"

        response = api_client.post(url, headers=auth_header, json=payload_twilio_sms)
        assert 200 == response.status_code

        response_body = json.loads(response.text)

        expected_response = {
            "key": "my_twilio_sms_config",
            "name": "twilio_sms",
            "service_type": MessagingServiceType.TWILIO_TEXT.value,
            "details": None,
        }
        assert expected_response == response_body


class TestPatchMessagingConfig:
    @pytest.fixture(scope="function")
    def url(self, messaging_config):
        return (V1_URL_PREFIX + MESSAGING_BY_KEY).format(
            config_key=messaging_config.key
        )

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            "key": "my_mailgun_messaging_config",
            "name": "mailgun new name",
            "service_type": MessagingServiceType.MAILGUN.value,
            "details": {MessagingServiceDetails.DOMAIN.value: "my.mailgun.domain"},
        }

    def test_patch_email_config_not_authenticated(self, api_client, payload, url):
        response = api_client.patch(url, headers={}, json=payload)
        assert 401 == response.status_code

    @pytest.mark.parametrize("auth_header", [[MESSAGING_READ]], indirect=True)
    def test_patch_email_config_incorrect_scope(
        self, auth_header, api_client, payload, url
    ):
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    @pytest.mark.usefixtures("messaging_config")
    @pytest.mark.parametrize(
        "auth_header", [[MESSAGING_CREATE_OR_UPDATE]], indirect=True
    )
    def test_patch_email_config_with_key_not_found(
        self, auth_header, api_client, payload
    ):
        url = (V1_URL_PREFIX + MESSAGING_BY_KEY).format(config_key="nonexistent_key")

        response = api_client.patch(url, headers=auth_header, json=payload)
        assert response.status_code == 404
        assert response.json() == {
            "detail": "No messaging config found with key nonexistent_key"
        }

    @pytest.mark.parametrize(
        "auth_header", [[MESSAGING_CREATE_OR_UPDATE]], indirect=True
    )
    def test_patch_email_config_with_key(self, auth_header, api_client, payload, url):
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        response_body = json.loads(response.text)

        expected_response = {
            "key": "my_mailgun_messaging_config",
            "name": "mailgun new name",
            "service_type": MessagingServiceType.MAILGUN.value,
            "details": {
                MessagingServiceDetails.API_VERSION.value: "v3",
                MessagingServiceDetails.DOMAIN.value: "my.mailgun.domain",
                MessagingServiceDetails.IS_EU_DOMAIN.value: False,
            },
        }
        assert expected_response == response_body


class TestPutMessagingConfigSecretsMailgun:
    @pytest.fixture(scope="function")
    def url(self, messaging_config):
        return (V1_URL_PREFIX + MESSAGING_SECRETS).format(
            config_key=messaging_config.key
        )

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            MessagingServiceSecrets.MAILGUN_API_KEY.value: "1345234524",
        }

    def test_put_config_secrets_unauthenticated(self, api_client, payload, url):
        response = api_client.put(url, headers={}, json=payload)
        assert 401 == response.status_code

    @pytest.mark.parametrize("auth_header", [[MESSAGING_READ]], indirect=True)
    def test_put_config_secrets_wrong_scope(
        self, auth_header, api_client, payload, url
    ):
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    @pytest.mark.parametrize(
        "auth_header", [[MESSAGING_CREATE_OR_UPDATE]], indirect=True
    )
    def test_put_config_secret_invalid_config(self, auth_header, api_client, payload):
        url = (V1_URL_PREFIX + MESSAGING_SECRETS).format(config_key="invalid_key")
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 404 == response.status_code

    @pytest.mark.parametrize(
        "auth_header", [[MESSAGING_CREATE_OR_UPDATE]], indirect=True
    )
    def test_update_with_invalid_secrets_key(self, auth_header, api_client, url):
        response = api_client.put(url, headers=auth_header, json={"bad_key": "12345"})

        assert response.status_code == 400
        assert response.json() == {
            "detail": [
                "field required ('mailgun_api_key',)",
                "extra fields not permitted ('bad_key',)",
            ]
        }

    @pytest.mark.parametrize(
        "auth_header", [[MESSAGING_CREATE_OR_UPDATE]], indirect=True
    )
    def test_put_config_secrets(
        self,
        auth_header,
        db,
        api_client,
        payload,
        url,
        messaging_config,
    ):
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
    def url(self, messaging_config_twilio_email):
        return (V1_URL_PREFIX + MESSAGING_SECRETS).format(
            config_key=messaging_config_twilio_email.key
        )

    @pytest.fixture(scope="function")
    def payload(self):
        return {MessagingServiceSecrets.TWILIO_API_KEY.value: "23p48btcpy14b"}

    @pytest.mark.parametrize(
        "auth_header", [[MESSAGING_CREATE_OR_UPDATE]], indirect=True
    )
    def test_put_config_secrets(
        self,
        auth_header,
        db,
        api_client,
        payload,
        url,
        messaging_config_twilio_email,
    ):
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


class TestPutMessagingConfigSecretTwilioSms:
    @pytest.fixture(scope="function")
    def url(self, messaging_config_twilio_sms):
        return (V1_URL_PREFIX + MESSAGING_SECRETS).format(
            config_key=messaging_config_twilio_sms.key
        )

    @pytest.mark.parametrize(
        "auth_header", [[MESSAGING_CREATE_OR_UPDATE]], indirect=True
    )
    def test_put_config_secrets_with_messaging_service_sid(
        self,
        auth_header,
        db,
        api_client,
        url,
        messaging_config_twilio_sms,
    ):
        payload = {
            MessagingServiceSecrets.TWILIO_ACCOUNT_SID.value: "234ct324",
            MessagingServiceSecrets.TWILIO_AUTH_TOKEN.value: "3rcuinhewrf",
            MessagingServiceSecrets.TWILIO_MESSAGING_SERVICE_SID.value: "asdfasdf",
        }
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

    @pytest.mark.parametrize(
        "auth_header", [[MESSAGING_CREATE_OR_UPDATE]], indirect=True
    )
    def test_put_config_secrets_with_sender_phone(
        self, auth_header, db, api_client, url, messaging_config_twilio_sms
    ):
        payload = {
            MessagingServiceSecrets.TWILIO_ACCOUNT_SID.value: "2asdf35tv5wsdf",
            MessagingServiceSecrets.TWILIO_AUTH_TOKEN.value: "23tc3",
            MessagingServiceSecrets.TWILIO_SENDER_PHONE_NUMBER.value: "+12345436543",
        }
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

    @pytest.mark.usefixtures("messaging_config_twilio_sms")
    @pytest.mark.parametrize(
        "auth_header", [[MESSAGING_CREATE_OR_UPDATE]], indirect=True
    )
    def test_put_config_secrets_with_sender_phone_incorrect_format(
        self, auth_header, api_client, url
    ):
        payload = {
            MessagingServiceSecrets.TWILIO_ACCOUNT_SID.value: "2asdf35tv5wsdf",
            MessagingServiceSecrets.TWILIO_AUTH_TOKEN.value: "23tc3",
            MessagingServiceSecrets.TWILIO_SENDER_PHONE_NUMBER.value: "12345436543",
        }
        response = api_client.put(url, headers=auth_header, json=payload)
        assert response.status_code == 400
        assert (
            f"Sender phone number must include country code, formatted like +15558675309 ('__root__',)"
            in response.json()["detail"]
        )

    @pytest.mark.usefixtures("messaging_config_twilio_sms")
    @pytest.mark.parametrize(
        "auth_header", [[MESSAGING_CREATE_OR_UPDATE]], indirect=True
    )
    def test_put_config_secrets_with_no_sender_phone_nor_messaging_service_id(
        self, auth_header, api_client, url
    ):
        payload = {
            MessagingServiceSecrets.TWILIO_ACCOUNT_SID.value: "2asdf35tv5wsdf",
            MessagingServiceSecrets.TWILIO_AUTH_TOKEN.value: "23tc3",
        }
        response = api_client.put(url, headers=auth_header, json=payload)
        assert response.status_code == 400
        assert (
            f"Either the twilio_messaging_service_sid or the twilio_sender_phone_number should be supplied. ('__root__',)"
            in response.json()["detail"]
        )


class TestGetMessagingConfigs:
    @pytest.fixture(scope="function")
    def url(self):
        return V1_URL_PREFIX + MESSAGING_CONFIG

    def test_get_configs_not_authenticated(self, api_client, url):
        response = api_client.get(url)
        assert 401 == response.status_code

    @pytest.mark.parametrize("auth_header", [[MESSAGING_DELETE]], indirect=True)
    def test_get_configs_wrong_scope(self, auth_header, api_client, url):
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    @pytest.mark.parametrize("auth_header", [[MESSAGING_READ]], indirect=True)
    def test_get_configs(self, auth_header, api_client, url, messaging_config):
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code

        expected_response = {
            "items": [
                {
                    "key": "my_mailgun_messaging_config",
                    "name": messaging_config.name,
                    "service_type": MessagingServiceType.MAILGUN.value,
                    "details": {
                        MessagingServiceDetails.API_VERSION.value: "v3",
                        MessagingServiceDetails.DOMAIN.value: "some.domain",
                        MessagingServiceDetails.IS_EU_DOMAIN.value: False,
                    },
                }
            ],
            "page": 1,
            "size": PAGE_SIZE,
            "total": 1,
        }
        response_body = json.loads(response.text)
        assert expected_response == response_body


class TestGetMessagingConfig:
    @pytest.fixture(scope="function")
    def url(self, messaging_config):
        return (V1_URL_PREFIX + MESSAGING_BY_KEY).format(
            config_key=messaging_config.key
        )

    def test_get_config_not_authenticated(self, url, api_client):
        response = api_client.get(url)
        assert 401 == response.status_code

    @pytest.mark.parametrize("auth_header", [[MESSAGING_DELETE]], indirect=True)
    def test_get_config_wrong_scope(self, auth_header, url, api_client):
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    @pytest.mark.usefixtures("messaging_config")
    @pytest.mark.parametrize("auth_header", [[MESSAGING_READ]], indirect=True)
    def test_get_config_invalid(self, auth_header, api_client):
        response = api_client.get(
            (V1_URL_PREFIX + MESSAGING_BY_KEY).format(config_key="invalid"),
            headers=auth_header,
        )
        assert 404 == response.status_code

    @pytest.mark.parametrize("auth_header", [[MESSAGING_READ]], indirect=True)
    def test_get_config(self, auth_header, url, api_client, messaging_config):
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200

        response_body = json.loads(response.text)

        assert response_body == {
            "key": "my_mailgun_messaging_config",
            "name": messaging_config.name,
            "service_type": MessagingServiceType.MAILGUN.value,
            "details": {
                MessagingServiceDetails.API_VERSION.value: "v3",
                MessagingServiceDetails.DOMAIN.value: "some.domain",
                MessagingServiceDetails.IS_EU_DOMAIN.value: False,
            },
        }


class TestDeleteConfig:
    @pytest.fixture(scope="function")
    def url(self, messaging_config):
        return (V1_URL_PREFIX + MESSAGING_BY_KEY).format(
            config_key=messaging_config.key
        )

    def test_delete_config_not_authenticated(self, url, api_client):
        response = api_client.delete(url)
        assert 401 == response.status_code

    @pytest.mark.parametrize("auth_header", [[MESSAGING_READ]], indirect=True)
    def test_delete_config_wrong_scope(self, auth_header, url, api_client):
        response = api_client.delete(url, headers=auth_header)
        assert 403 == response.status_code

    @pytest.mark.parametrize("auth_header", [[MESSAGING_DELETE]], indirect=True)
    def test_delete_config_invalid(self, auth_header, api_client):
        response = api_client.delete(
            (V1_URL_PREFIX + MESSAGING_BY_KEY).format(config_key="invalid"),
            headers=auth_header,
        )
        assert 404 == response.status_code

    @pytest.mark.parametrize("auth_header", [[MESSAGING_DELETE]], indirect=True)
    def test_delete_config(self, auth_header, db, url, api_client):
        # Creating new config, so we don't run into issues trying to clean up a deleted fixture
        twilio_sms_config = MessagingConfig.create(
            db=db,
            data={
                "key": "my_twilio_sms_config",
                "name": "twilio_sms",
                "service_type": MessagingServiceType.TWILIO_TEXT,
            },
        )
        url = (V1_URL_PREFIX + MESSAGING_BY_KEY).format(
            config_key=twilio_sms_config.key
        )
        response = api_client.delete(url, headers=auth_header)
        assert response.status_code == 204

        db.expunge_all()
        config = db.query(MessagingConfig).filter_by(key=twilio_sms_config.key).first()
        assert config is None
