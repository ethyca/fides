import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fides.api.models.manual_webhook import AccessManualWebhook
from fides.common.api.scope_registry import (
    CONNECTION_READ,
    STORAGE_READ,
    WEBHOOK_CREATE_OR_UPDATE,
    WEBHOOK_DELETE,
    WEBHOOK_READ,
)
from fides.common.api.v1.urn_registry import (
    ACCESS_MANUAL_WEBHOOK,
    ACCESS_MANUAL_WEBHOOKS,
    CONNECTION_TEST,
    V1_URL_PREFIX,
)


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

        expected_fields = [
            {
                "pii_field": "email",
                "dsr_package_label": "email",
                "data_categories": ["user.contact.email"],
                "types": ["string"],
            },
            {
                "pii_field": "Last Name",
                "dsr_package_label": "last_name",
                "data_categories": ["user.name"],
                "types": ["string"],
            },
        ]

        assert resp["fields"] == expected_fields

        connection_config_details = resp["connection_config"]
        assert connection_config_details["key"] == integration_manual_webhook_config.key
        assert connection_config_details["connection_type"] == "manual_webhook"
        assert connection_config_details["access"] == "read"
        assert connection_config_details["created_at"] is not None
        assert connection_config_details["updated_at"] is not None
        assert connection_config_details["secrets"] is None

    def test_get_manual_webhook_with_multiple_types(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        integration_manual_webhook_config,
    ):
        """Test retrieving a manual webhook with multiple types per field"""
        manual_webhook = AccessManualWebhook.create(
            db=db,
            data={
                "connection_config_id": integration_manual_webhook_config.id,
                "fields": [
                    {
                        "pii_field": "medical_records",
                        "dsr_package_label": "medical_records",
                        "data_categories": ["user.medical"],
                        "types": ["string", "file"],
                    }
                ],
            },
        )

        auth_header = generate_auth_header([WEBHOOK_READ])
        response = api_client.get(url, headers=auth_header)

        assert response.status_code == 200
        resp = response.json()

        assert resp["fields"][0]["types"] == ["string", "file"]

        manual_webhook.delete(db)


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
                {
                    "pii_field": "First name",
                    "dsr_package_label": None,
                    "data_categories": ["user.name"],
                    "types": ["string"],
                },
                {
                    "pii_field": "Last name",
                    "dsr_package_label": "last_name",
                    "data_categories": ["user.name"],
                    "types": ["string"],
                },
                {
                    "pii_field": "Order number",
                    "dsr_package_label": "order_number",
                    "data_categories": None,
                    "types": ["string"],
                },
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
            == "String should have at most 200 characters"
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
        assert (
            response.json()["detail"][0]["msg"]
            == "Value error, pii_fields must be unique"
        )

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
            == "String should have at least 1 character"
        )

    def test_post_access_manual_webhook_pii_label_spaces(
        self, db, api_client, url, generate_auth_header
    ):
        payload = {
            "fields": [
                {"pii_field": "first_name", "dsr_package_label": "First Name"},
                {"pii_field": "   ", "dsr_package_label": "label"},
            ]
        }
        auth_header = generate_auth_header([WEBHOOK_CREATE_OR_UPDATE])
        response = api_client.post(url, headers=auth_header, json=payload)
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "String should have at least 1 character"
        )

    def test_post_access_manual_webhook_dsr_package_labels_empty_string(
        self, db, api_client, url, generate_auth_header
    ):
        payload = {
            "fields": [
                {
                    "pii_field": "first_name",
                    "dsr_package_label": "First Name",
                    "data_categories": ["user.name"],
                },
                {
                    "pii_field": "last_name",
                    "dsr_package_label": "",
                    "data_categories": ["user.name"],
                },
            ]
        }
        auth_header = generate_auth_header([WEBHOOK_CREATE_OR_UPDATE])
        response = api_client.post(url, headers=auth_header, json=payload)
        assert response.status_code == 201
        assert response.json()["fields"] == [
            {
                "pii_field": "first_name",
                "dsr_package_label": "First Name",
                "data_categories": ["user.name"],
                "types": ["string"],
            },
            {
                "pii_field": "last_name",
                "dsr_package_label": "last_name",
                "data_categories": ["user.name"],
                "types": ["string"],
            },
        ]

    def test_post_access_manual_webhook_dsr_package_labels_spaces(
        self, db, api_client, url, generate_auth_header
    ):
        payload = {
            "fields": [
                {
                    "pii_field": "first_name",
                    "dsr_package_label": "First Name",
                    "data_categories": ["user.name"],
                    "types": ["string"],
                },
                {
                    "pii_field": "last_name",
                    "dsr_package_label": "  ",
                    "data_categories": ["user.name"],
                    "types": ["string"],
                },
            ]
        }
        auth_header = generate_auth_header([WEBHOOK_CREATE_OR_UPDATE])
        response = api_client.post(url, headers=auth_header, json=payload)
        assert response.status_code == 201
        assert response.json()["fields"] == [
            {
                "pii_field": "first_name",
                "dsr_package_label": "First Name",
                "data_categories": ["user.name"],
                "types": ["string"],
            },
            {
                "pii_field": "last_name",
                "dsr_package_label": "last_name",
                "data_categories": ["user.name"],
                "types": ["string"],
            },
        ]

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
            == "List should have at least 1 item after validation, not 0"
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
            {
                "pii_field": "First name",
                "dsr_package_label": "first_name",
                "data_categories": ["user.name"],
                "types": ["string"],
            },
            {
                "pii_field": "Last name",
                "dsr_package_label": "last_name",
                "data_categories": ["user.name"],
                "types": ["string"],
            },
            {
                "pii_field": "Order number",
                "dsr_package_label": "order_number",
                "data_categories": None,
                "types": ["string"],
            },
        ]
        connection_config_details = resp["connection_config"]
        assert connection_config_details["key"] == integration_manual_webhook_config.key
        assert connection_config_details["connection_type"] == "manual_webhook"
        assert connection_config_details["access"] == "read"
        assert connection_config_details["created_at"] is not None
        assert connection_config_details["updated_at"] is not None
        assert connection_config_details["secrets"] is None

        manual_webhook = AccessManualWebhook.get(db=db, object_id=resp["id"])
        manual_webhook.delete(db)

    def test_post_manual_webhook_with_multiple_types(
        self,
        db: Session,
        api_client: TestClient,
        url,
        generate_auth_header,
        integration_manual_webhook_config,
    ):
        """Test creating a manual webhook with multiple types per field"""
        auth_header = generate_auth_header([WEBHOOK_CREATE_OR_UPDATE])
        payload = {
            "fields": [
                {
                    "pii_field": "medical_records",
                    "dsr_package_label": "medical_records",
                    "data_categories": ["user.medical"],
                    "types": ["string", "file"],
                },
                {
                    "pii_field": "patient_notes",
                    "dsr_package_label": "patient_notes",
                    "data_categories": ["user.medical.notes"],
                    "types": ["string"],
                },
            ]
        }
        response = api_client.post(url, headers=auth_header, json=payload)
        assert response.status_code == 201
        resp = response.json()

        assert resp["fields"][0]["types"] == ["string", "file"]
        assert resp["fields"][1]["types"] == ["string"]

    def test_post_manual_webhook_invalid_types(
        self,
        db: Session,
        api_client: TestClient,
        url,
        generate_auth_header,
    ):
        """Test validation of field types"""
        auth_header = generate_auth_header([WEBHOOK_CREATE_OR_UPDATE])
        payload = {
            "fields": [
                {
                    "pii_field": "test_field",
                    "dsr_package_label": "test_field",
                    "types": ["invalid_type"],
                }
            ]
        }
        response = api_client.post(url, headers=auth_header, json=payload)
        assert response.status_code == 422
        assert (
            "Input should be 'string' or 'file'" in response.json()["detail"][0]["msg"]
        )


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
                {
                    "pii_field": "New Field",
                    "dsr_package_label": None,
                    "data_categories": None,
                    "types": ["string"],
                },
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
                {
                    "pii_field": "New Field",
                    "dsr_package_label": None,
                    "data_categories": [
                        "user.contact.address.street",
                        "user.contact.address.city",
                        "user.contact.address.state",
                    ],
                    "types": ["string", "file"],
                },
            ]
        }

        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        resp = response.json()

        assert resp["fields"] == [
            {
                "pii_field": "New Field",
                "dsr_package_label": "new_field",
                "data_categories": [
                    "user.contact.address.street",
                    "user.contact.address.city",
                    "user.contact.address.state",
                ],
                "types": ["string", "file"],
            },
        ]
        connection_config_details = resp["connection_config"]
        assert connection_config_details["key"] == integration_manual_webhook_config.key
        assert connection_config_details["connection_type"] == "manual_webhook"
        assert connection_config_details["access"] == "read"
        assert connection_config_details["created_at"] is not None
        assert connection_config_details["updated_at"] is not None
        assert connection_config_details["secrets"] is None

    def test_patch_manual_webhook_with_multiple_types(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
    ):
        """Test updating a manual webhook with multiple types per field"""
        auth_header = generate_auth_header([WEBHOOK_CREATE_OR_UPDATE])
        payload = {
            "fields": [
                {
                    "pii_field": "medical_records",
                    "dsr_package_label": "medical_records",
                    "data_categories": ["user.medical"],
                    "types": ["string", "file"],
                }
            ]
        }

        response = api_client.patch(url, headers=auth_header, json=payload)
        assert response.status_code == 200

        resp = response.json()
        assert resp["fields"][0]["types"] == ["string", "file"]

    def test_patch_manual_webhook_backward_compatibility(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
    ):
        """Test that old-style fields without types still work"""
        auth_header = generate_auth_header([WEBHOOK_CREATE_OR_UPDATE])
        payload = {
            "fields": [
                {
                    "pii_field": "email",
                    "dsr_package_label": "email",
                    "data_categories": ["user.contact.email"],
                    "types": ["string"],
                }
            ]
        }

        response = api_client.patch(url, headers=auth_header, json=payload)
        assert response.status_code == 200

        resp = response.json()
        assert resp["fields"][0]["types"] == ["string"]  # Default type


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
            {
                "pii_field": "email",
                "dsr_package_label": "email",
                "data_categories": ["user.contact.email"],
                "types": ["string"],
            },
            {
                "pii_field": "Last Name",
                "dsr_package_label": "last_name",
                "data_categories": ["user.name"],
                "types": ["string"],
            },
        ]

        connection_config_details = resp["connection_config"]
        assert connection_config_details["key"] == integration_manual_webhook_config.key
        assert connection_config_details["connection_type"] == "manual_webhook"
        assert connection_config_details["access"] == "read"
        assert connection_config_details["created_at"] is not None
        assert connection_config_details["updated_at"] is not None
        assert connection_config_details["secrets"] is None


class TestManualWebhookTest:
    @pytest.fixture(scope="function")
    def url(self, integration_manual_webhook_config) -> str:
        return V1_URL_PREFIX + CONNECTION_TEST.format(
            connection_key=integration_manual_webhook_config.key
        )

    def test_connection_test_manual_webhook_not_authenticated(
        self, api_client: TestClient, url
    ):
        response = api_client.get(url, headers={})
        assert 401 == response.status_code

    def test_connection_test_manual_webhook_wrong_scopes(
        self, api_client: TestClient, url, generate_auth_header
    ):
        auth_header = generate_auth_header([STORAGE_READ])

        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_connection_test_manual_webhook_no_webhook_resource(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        integration_manual_webhook_config,
    ):
        auth_header = generate_auth_header([CONNECTION_READ])

        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code
        assert response.json()["test_status"] == "failed"

    def test_connection_test_manual_webhook_no_webhook_fields(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        integration_manual_webhook_config,
        access_manual_webhook,
    ):
        auth_header = generate_auth_header([CONNECTION_READ])
        access_manual_webhook.fields = None
        access_manual_webhook.save(db)

        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code
        assert response.json()["test_status"] == "failed"

    def test_connection_test_manual_webhook(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
    ):
        auth_header = generate_auth_header([CONNECTION_READ])

        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code
        assert response.json()["test_status"] == "succeeded"

    def test_manual_webhook_backwards_compatibility(
        self,
        db: Session,
        api_client: TestClient,
        url,
        generate_auth_header,
        integration_manual_webhook_config,
    ):
        """Test that old-style fields without types still work"""
        # Create a webhook with old-style fields (no types)
        manual_webhook = AccessManualWebhook.create(
            db=db,
            data={
                "connection_config_id": integration_manual_webhook_config.id,
                "fields": [
                    {
                        "pii_field": "email",
                        "dsr_package_label": "email",
                        "data_categories": ["user.contact.email"],
                    }
                ],
            },
        )

        auth_header = generate_auth_header([WEBHOOK_READ])
        response = api_client.get(url, headers=auth_header)

        assert response.status_code == 200
        resp = response.json()

        # Verify that the field got a default type of "string"
        assert resp["fields"][0]["types"] == ["string"]

        manual_webhook.delete(db)


class TestManualWebhookBackwardsCompatibility:
    def test_field_definitions_backwards_compatibility(
        self,
        db: Session,
        integration_manual_webhook_config,
    ):
        """Test that field definitions work with both old and new style fields"""
        # Create a webhook with old-style fields (no types)
        manual_webhook = AccessManualWebhook.create(
            db=db,
            data={
                "connection_config_id": integration_manual_webhook_config.id,
                "fields": [
                    {
                        "pii_field": "email",
                        "dsr_package_label": "email",
                        "data_categories": ["user.contact.email"],
                    },
                    {
                        "pii_field": "document",
                        "dsr_package_label": "document",
                        "data_categories": ["user.documents"],
                        "types": ["file"],  # New style field
                    },
                ],
            },
        )

        try:
            # Test access field definitions
            access_fields = manual_webhook.access_field_definitions()
            assert "email" in access_fields
            assert "document" in access_fields
            assert access_fields["email"] == (Optional[str], None)
            assert access_fields["document"] == (Optional[str], None)

            # Test erasure field definitions
            erasure_fields = manual_webhook.erasure_field_definitions()
            assert (
                "email" in erasure_fields
            )  # Old field defaults to string, so included
            assert "document" not in erasure_fields  # File type field not included
            assert erasure_fields["email"] == (Optional[bool], None)

            # Test that the schema generation works
            schema = manual_webhook.fields_schema
            assert "email" in schema.schema()["properties"]
            assert "document" in schema.schema()["properties"]

            erasure_schema = manual_webhook.erasure_fields_schema
            assert "email" in erasure_schema.schema()["properties"]
            assert "document" not in erasure_schema.schema()["properties"]

        finally:
            manual_webhook.delete(db)

    def test_mixed_field_types_compatibility(
        self,
        db: Session,
        integration_manual_webhook_config,
    ):
        """Test that fields can handle mixed types in both old and new formats"""
        manual_webhook = AccessManualWebhook.create(
            db=db,
            data={
                "connection_config_id": integration_manual_webhook_config.id,
                "fields": [
                    {
                        "pii_field": "name",
                        "dsr_package_label": "name",
                        "data_categories": ["user.name"],
                    },
                    {
                        "pii_field": "medical_records",
                        "dsr_package_label": "medical_records",
                        "data_categories": ["user.medical"],
                        "types": ["string", "file"],
                    },
                ],
            },
        )

        try:
            # Test that old style field defaults to string
            access_fields = manual_webhook.access_field_definitions()
            assert "name" in access_fields
            assert "medical_records" in access_fields

            # Test that both fields appear in erasure fields since they both support string
            erasure_fields = manual_webhook.erasure_field_definitions()
            assert "name" in erasure_fields
            assert "medical_records" in erasure_fields

            # Verify schema generation works for mixed fields
            schema = manual_webhook.fields_schema
            properties = schema.schema()["properties"]
            assert "name" in properties
            assert "medical_records" in properties

        finally:
            manual_webhook.delete(db)
