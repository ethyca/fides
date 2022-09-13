import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fidesops.ops.api.v1.scope_registry import (
    STORAGE_READ,
    WEBHOOK_CREATE_OR_UPDATE,
    WEBHOOK_DELETE,
    WEBHOOK_READ,
)
from fidesops.ops.api.v1.urn_registry import (
    ACCESS_MANUAL_WEBHOOK,
    ACCESS_MANUAL_WEBHOOKS,
    V1_URL_PREFIX,
)
from fidesops.ops.models.manual_webhook import AccessManualWebhook


class TestGetAccessManualWebhook:
    @pytest.fixture(scope="function")
    def url(self, integration_manual_webhook_config) -> str:
        path = V1_URL_PREFIX + ACCESS_MANUAL_WEBHOOK
        path_params = {"connection_key": integration_manual_webhook_config.key}
        return path.format(**path_params)

    def test_get_manual_webhook_not_authenticated(self, api_client: TestClient, url):
        response = api_client.get(url, headers={})
        assert 401 == response.status_code

    def test_get_manual_webhook_wrong_scopes(
        self, api_client: TestClient, url, generate_auth_header
    ):
        auth_header = generate_auth_header([STORAGE_READ])

        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_get_manual_webhook_does_not_exist(
        self, api_client: TestClient, url, generate_auth_header
    ):
        auth_header = generate_auth_header([WEBHOOK_READ])

        response = api_client.get(url, headers=auth_header)
        assert 404 == response.status_code
        assert (
            response.json()["detail"]
            == "No access manual webhook exists for connection config with key 'manual_webhook_example'"
        )

    def test_try_to_get_manual_webhook_from_postgres_connector(
        self, api_client: TestClient, generate_auth_header, connection_config
    ):
        auth_header = generate_auth_header([WEBHOOK_READ])
        url = V1_URL_PREFIX + ACCESS_MANUAL_WEBHOOK.format(
            connection_key=connection_config.key
        )

        response = api_client.get(url, headers=auth_header)
        assert 404 == response.status_code
        assert (
            response.json()["detail"]
            == "Can't access manual webhooks for ConnectionConfigs of type 'postgres'"
        )

    def test_get_manual_webhook(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
    ):
        auth_header = generate_auth_header([WEBHOOK_READ])

        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code

        resp = response.json()

        assert resp["fields"] == [
            {"pii_field": "email", "dsr_package_label": "email"},
            {"pii_field": "Last Name", "dsr_package_label": "last_name"},
        ]
        connection_config_details = resp["connection_config"]
        assert connection_config_details["key"] == integration_manual_webhook_config.key
        assert connection_config_details["connection_type"] == "manual_webhook"
        assert connection_config_details["access"] == "read"
        assert connection_config_details["created_at"] is not None
        assert connection_config_details["updated_at"] is not None
        assert "secrets" not in connection_config_details


class TestPostAccessManualWebhook:
    @pytest.fixture(scope="function")
    def url(self, integration_manual_webhook_config) -> str:
        path = V1_URL_PREFIX + ACCESS_MANUAL_WEBHOOK
        path_params = {"connection_key": integration_manual_webhook_config.key}
        return path.format(**path_params)

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            "fields": [
                {"pii_field": "First name", "dsr_package_label": None},
                {"pii_field": "Last name", "dsr_package_label": "last_name"},
                {"pii_field": "Order number", "dsr_package_label": "order_number"},
            ]
        }

    def test_post_manual_webhook_not_authenticated(
        self, api_client: TestClient, payload, url
    ):
        response = api_client.post(url, headers={}, json=payload)
        assert 401 == response.status_code

    def test_post_manual_webhook_incorrect_scope(
        self,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([WEBHOOK_READ])
        response = api_client.post(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_post_access_manual_webhook_already_exists(
        self, db, api_client, url, payload, generate_auth_header, access_manual_webhook
    ):
        auth_header = generate_auth_header([WEBHOOK_CREATE_OR_UPDATE])
        response = api_client.post(url, headers=auth_header, json=payload)
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "An Access Manual Webhook already exists for ConnectionConfig 'manual_webhook_example'."
        )

    def test_access_manual_webhook_pii_field_too_long(
        self, db, api_client, url, generate_auth_header
    ):
        payload = {
            "fields": [{"pii_field": "hello" * 100, "dsr_package_label": "First Name"}]
        }
        auth_header = generate_auth_header([WEBHOOK_CREATE_OR_UPDATE])
        response = api_client.post(url, headers=auth_header, json=payload)
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "ensure this value has at most 200 characters"
        )

    def test_post_manual_webhook_duplicate_fields(
        self, db, api_client, url, generate_auth_header
    ):
        payload = {
            "fields": [
                {"pii_field": "first_name", "dsr_package_label": "First Name"},
                {"pii_field": "first_name", "dsr_package_label": "First Name"},
            ]
        }
        auth_header = generate_auth_header([WEBHOOK_CREATE_OR_UPDATE])
        response = api_client.post(url, headers=auth_header, json=payload)
        assert response.status_code == 422
        assert response.json()["detail"][0]["msg"] == "pii_fields must be unique"

    def test_post_access_manual_webhook_fields_empty_string(
        self, db, api_client, url, generate_auth_header
    ):
        payload = {
            "fields": [
                {"pii_field": "first_name", "dsr_package_label": "First Name"},
                {"pii_field": "", "dsr_package_label": "bad_label"},
            ]
        }
        auth_header = generate_auth_header([WEBHOOK_CREATE_OR_UPDATE])
        response = api_client.post(url, headers=auth_header, json=payload)
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "ensure this value has at least 1 characters"
        )

    def test_post_access_manual_webhook_wrong_connection_config_type(
        self, connection_config, payload, generate_auth_header, api_client
    ):
        url = V1_URL_PREFIX + ACCESS_MANUAL_WEBHOOK.format(
            connection_key=connection_config.key
        )
        auth_header = generate_auth_header([WEBHOOK_CREATE_OR_UPDATE])
        response = api_client.post(url, headers=auth_header, json=payload)
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "You can only create manual webhooks for ConnectionConfigs of type 'manual_webhook'."
        )

    def test_post_webhook_no_fields(
        self, connection_config, payload, generate_auth_header, api_client, url
    ):
        auth_header = generate_auth_header([WEBHOOK_CREATE_OR_UPDATE])
        response = api_client.post(url, headers=auth_header, json={"fields": []})

        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "ensure this value has at least 1 items"
        )

    def test_post_manual_webhook(
        self,
        db: Session,
        api_client: TestClient,
        url,
        payload,
        generate_auth_header,
        integration_manual_webhook_config,
    ):
        auth_header = generate_auth_header([WEBHOOK_CREATE_OR_UPDATE])
        response = api_client.post(url, headers=auth_header, json=payload)
        assert response.status_code == 201
        resp = response.json()

        assert resp["fields"] == [
            {"pii_field": "First name", "dsr_package_label": "first_name"},
            {"pii_field": "Last name", "dsr_package_label": "last_name"},
            {"pii_field": "Order number", "dsr_package_label": "order_number"},
        ]
        connection_config_details = resp["connection_config"]
        assert connection_config_details["key"] == integration_manual_webhook_config.key
        assert connection_config_details["connection_type"] == "manual_webhook"
        assert connection_config_details["access"] == "read"
        assert connection_config_details["created_at"] is not None
        assert connection_config_details["updated_at"] is not None
        assert "secrets" not in connection_config_details

        manual_webhook = AccessManualWebhook.get(db=db, object_id=resp["id"])
        manual_webhook.delete(db)


class TestPatchAccessManualWebhook:
    @pytest.fixture(scope="function")
    def url(self, integration_manual_webhook_config) -> str:
        path = V1_URL_PREFIX + ACCESS_MANUAL_WEBHOOK
        path_params = {"connection_key": integration_manual_webhook_config.key}
        return path.format(**path_params)

    def test_patch_manual_webhook_not_authenticated(self, api_client: TestClient, url):
        response = api_client.patch(url, headers={})
        assert 401 == response.status_code

    def test_patch_manual_webhook_wrong_scopes(
        self, api_client: TestClient, url, generate_auth_header
    ):
        auth_header = generate_auth_header([WEBHOOK_READ])

        response = api_client.patch(url, headers=auth_header)
        assert 403 == response.status_code

    def test_patch_manual_webhook_does_not_exist(
        self, api_client: TestClient, url, generate_auth_header
    ):
        auth_header = generate_auth_header([WEBHOOK_CREATE_OR_UPDATE])
        payload = {
            "fields": [
                {"pii_field": "New Field", "dsr_package_label": None},
            ]
        }

        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 404 == response.status_code
        assert (
            response.json()["detail"]
            == "No access manual webhook exists for connection config with key 'manual_webhook_example'"
        )

    def test_patch_manual_webhook(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
    ):
        auth_header = generate_auth_header([WEBHOOK_CREATE_OR_UPDATE])
        payload = {
            "fields": [
                {"pii_field": "New Field", "dsr_package_label": None},
            ]
        }

        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        resp = response.json()

        assert resp["fields"] == [
            {"pii_field": "New Field", "dsr_package_label": "new_field"},
        ]
        connection_config_details = resp["connection_config"]
        assert connection_config_details["key"] == integration_manual_webhook_config.key
        assert connection_config_details["connection_type"] == "manual_webhook"
        assert connection_config_details["access"] == "read"
        assert connection_config_details["created_at"] is not None
        assert connection_config_details["updated_at"] is not None
        assert "secrets" not in connection_config_details


class TestDeleteAccessManualWebhook:
    @pytest.fixture(scope="function")
    def url(self, integration_manual_webhook_config) -> str:
        path = V1_URL_PREFIX + ACCESS_MANUAL_WEBHOOK
        path_params = {"connection_key": integration_manual_webhook_config.key}
        return path.format(**path_params)

    def test_delete_manual_webhook_not_authenticated(self, api_client: TestClient, url):
        response = api_client.delete(url, headers={})
        assert 401 == response.status_code

    def test_delete_manual_webhook_wrong_scopes(
        self, api_client: TestClient, url, generate_auth_header
    ):
        auth_header = generate_auth_header([WEBHOOK_READ])

        response = api_client.delete(url, headers=auth_header)
        assert 403 == response.status_code

    def test_delete_manual_webhook_does_not_exist(
        self, api_client: TestClient, url, generate_auth_header
    ):
        auth_header = generate_auth_header([WEBHOOK_DELETE])

        response = api_client.delete(url, headers=auth_header)
        assert 404 == response.status_code
        assert (
            response.json()["detail"]
            == "No access manual webhook exists for connection config with key 'manual_webhook_example'"
        )

    def test_delete_manual_webhook(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
    ):
        assert integration_manual_webhook_config.access_manual_webhook is not None
        auth_header = generate_auth_header([WEBHOOK_DELETE])

        response = api_client.delete(url, headers=auth_header)
        assert 204 == response.status_code
        db.refresh(integration_manual_webhook_config)
        assert integration_manual_webhook_config.access_manual_webhook is None


class TestGetAccessManualWebhooks:
    @pytest.fixture(scope="function")
    def url(self, integration_manual_webhook_config) -> str:
        return V1_URL_PREFIX + ACCESS_MANUAL_WEBHOOKS

    def test_get_manual_webhook_not_authenticated(self, api_client: TestClient, url):
        response = api_client.get(url, headers={})
        assert 401 == response.status_code

    def test_get_manual_webhook_wrong_scopes(
        self, api_client: TestClient, url, generate_auth_header
    ):
        auth_header = generate_auth_header([STORAGE_READ])

        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_disabled_webhooks(
        self,
        db,
        api_client,
        url,
        generate_auth_header,
        integration_manual_webhook_config,
        access_manual_webhook,
    ):
        integration_manual_webhook_config.disabled = True
        integration_manual_webhook_config.save(db)

        auth_header = generate_auth_header([WEBHOOK_READ])

        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code

        assert len(response.json()) == 0

    def test_get_manual_webhooks(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
    ):
        auth_header = generate_auth_header([WEBHOOK_READ])

        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code

        assert len(response.json()) == 1
        resp = response.json()[0]

        assert resp["fields"] == [
            {"pii_field": "email", "dsr_package_label": "email"},
            {"pii_field": "Last Name", "dsr_package_label": "last_name"},
        ]
        connection_config_details = resp["connection_config"]
        assert connection_config_details["key"] == integration_manual_webhook_config.key
        assert connection_config_details["connection_type"] == "manual_webhook"
        assert connection_config_details["access"] == "read"
        assert connection_config_details["created_at"] is not None
        assert connection_config_details["updated_at"] is not None
        assert "secrets" not in connection_config_details
