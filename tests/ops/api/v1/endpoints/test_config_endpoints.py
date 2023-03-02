from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fides.api.ops.api.v1 import scope_registry as scopes
from fides.api.ops.api.v1 import urn_registry as urls
from fides.api.ops.models.application_config import ApplicationConfig
from fides.api.ops.schemas.storage.storage import StorageType


class TestPatchApplicationConfig:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return urls.V1_URL_PREFIX + urls.CONFIG

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            "storage": {"active_default_storage_type": StorageType.s3.value},
            "notifications": {
                "notification_service_type": "TWILIO_TEXT",
                "send_request_completion_notification": True,
                "send_request_receipt_notification": True,
                "send_request_review_notification": True,
            },
            "execution": {
                "subject_identity_verification_required": True,
                "require_manual_request_approval": True,
            },
        }

    def test_patch_application_config_unauthenticated(
        self, api_client: TestClient, payload, url
    ):
        response = api_client.patch(url, headers={}, json=payload)
        assert 401 == response.status_code

    def test_patch_application_config_wrong_scope(
        self, api_client: TestClient, payload, url, generate_auth_header
    ):
        auth_header = generate_auth_header([scopes.CONFIG_READ])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_patch_application_config_with_invalid_key(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        payload: dict[str, Any],
    ):
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.patch(
            url, headers=auth_header, json={"storage": {"bad_key": "s3"}}
        )
        assert response.status_code == 422

        response = api_client.patch(
            url,
            headers=auth_header,
            json={"bad_key": {"active_default_storage_type": "s3"}},
        )
        assert response.status_code == 422

        # now test payload with both a good key and a bad key - should be rejected
        payload["bad_key"] = "12345"
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert response.status_code == 422

        # and a nested bad key
        payload.pop("bad_key")
        payload["storage"]["bad_key"] = "12345"
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert response.status_code == 422

    def test_patch_application_config_with_invalid_value(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.patch(
            url,
            headers=auth_header,
            json={"storage": {"active_default_storage_type": 33}},
        )
        assert response.status_code == 422

        response = api_client.patch(
            url,
            headers=auth_header,
            json={"storage": {"active_default_storage_type": "fake_storage_type"}},
        )
        assert response.status_code == 422

        # gcs is valid storage type but not allowed currently
        # as an `active_default_storage_type``
        response = api_client.patch(
            url,
            headers=auth_header,
            json={"storage": {"active_default_storage_type": StorageType.gcs.value}},
        )
        assert response.status_code == 422

    def test_patch_application_config_empty_body(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
    ):
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.patch(
            url,
            headers=auth_header,
            json={},
        )
        assert response.status_code == 422

        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.patch(
            url,
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_patch_application_config(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        payload,
        db: Session,
    ):
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.patch(
            url,
            headers=auth_header,
            json=payload,
        )
        assert response.status_code == 200
        response_settings = response.json()
        assert response_settings["storage"] == payload["storage"]
        assert response_settings["execution"] == payload["execution"]
        assert response_settings["notifications"] == payload["notifications"]
        db_settings = db.query(ApplicationConfig).first()
        assert db_settings.api_set["storage"] == payload["storage"]
        assert db_settings.api_set["execution"] == payload["execution"]
        assert db_settings.api_set["notifications"] == payload["notifications"]

        # try PATCHing a single property
        updated_payload = {"storage": {"active_default_storage_type": "local"}}
        response = api_client.patch(
            url,
            headers=auth_header,
            json=updated_payload,
        )
        assert response.status_code == 200
        response_settings = response.json()
        assert response_settings["storage"]["active_default_storage_type"] == "local"
        # ensure other properties were not impacted
        assert response_settings["execution"] == payload["execution"]
        assert response_settings["notifications"] == payload["notifications"]
        db.refresh(db_settings)
        # ensure property was updated on backend
        assert db_settings.api_set["storage"]["active_default_storage_type"] == "local"
        # but other properties were not impacted
        assert db_settings.api_set["execution"] == payload["execution"]
        assert db_settings.api_set["notifications"] == payload["notifications"]

        # try PATCHing multiple properties in the same nested object
        updated_payload = {
            "execution": {"subject_identity_verification_required": False},
            "notifications": {
                "notification_service_type": "MAILGUN",
                "send_request_completion_notification": False,
            },
        }
        response = api_client.patch(
            url,
            headers=auth_header,
            json=updated_payload,
        )
        assert response.status_code == 200
        response_settings = response.json()
        assert response_settings["storage"]["active_default_storage_type"] == "local"
        assert (
            response_settings["execution"]["subject_identity_verification_required"]
            is False
        )
        assert (
            response_settings["notifications"]["notification_service_type"] == "MAILGUN"
        )
        assert (
            response_settings["notifications"]["send_request_completion_notification"]
            is False
        )
        # ensure other properties were not impacted
        assert (
            response_settings["notifications"]["send_request_receipt_notification"]
            is True
        )

        db.refresh(db_settings)
        # ensure property was updated on backend
        assert db_settings.api_set["storage"]["active_default_storage_type"] == "local"
        assert (
            db_settings.api_set["execution"]["subject_identity_verification_required"]
            is False
        )
        assert (
            db_settings.api_set["notifications"]["notification_service_type"]
            == "MAILGUN"
        )
        assert (
            db_settings.api_set["notifications"]["send_request_completion_notification"]
            is False
        )
        # ensure other properties were not impacted
        assert (
            db_settings.api_set["notifications"]["send_request_receipt_notification"]
            is True
        )

    def test_patch_application_config_notifications_properties(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        payload,
        db: Session,
    ):

        payload = {"notifications": {"send_request_completion_notification": False}}
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.patch(
            url,
            headers=auth_header,
            json=payload,
        )
        assert response.status_code == 200
        response_settings = response.json()
        # this should look exactly like the payload - no additional properties
        assert response_settings["notifications"] == payload["notifications"]
        assert "execution" not in response_settings
        db_settings = db.query(ApplicationConfig).first()
        # this should look exactly like the payload - no additional properties
        assert db_settings.api_set["notifications"] == payload["notifications"]
        assert "execution" not in db_settings.api_set

    def test_patch_application_config_invalid_notification_type(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        payload,
        db: Session,
    ):

        payload = {
            "notifications": {"notification_service_type": "invalid_service_type"}
        }
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.patch(
            url,
            headers=auth_header,
            json=payload,
        )
        assert response.status_code == 422


class TestGetApplicationConfigApiSet:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return urls.V1_URL_PREFIX + urls.CONFIG

    @pytest.fixture(scope="function")
    def payload(self):
        return {"storage": {"active_default_storage_type": StorageType.s3.value}}

    @pytest.fixture(scope="function")
    def payload_single_notification_property(self):
        return {"notifications": {"notification_service_type": "twilio_email"}}

    def test_get_application_config_unauthenticated(self, api_client: TestClient, url):
        response = api_client.get(url, headers={})
        assert 401 == response.status_code

    def test_get_application_config_wrong_scope(
        self, api_client: TestClient, url, generate_auth_header
    ):
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_get_application_config_empty_settings(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
    ):
        auth_header = generate_auth_header([scopes.CONFIG_READ])
        response = api_client.get(
            url,
            headers=auth_header,
            params={"api_set": True},
        )
        assert response.status_code == 200
        assert response.json() == {}

    def test_get_application_config(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        db: Session,
        payload,
        payload_single_notification_property,
    ):
        # first we PATCH in some settings
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.patch(
            url,
            headers=auth_header,
            json=payload,
        )
        assert response.status_code == 200

        # then we test that we can GET them
        auth_header = generate_auth_header([scopes.CONFIG_READ])
        response = api_client.request(
            "GET",
            url,
            headers=auth_header,
            params={"api_set": True},
        )
        assert response.status_code == 200
        response_settings = response.json()
        assert (
            response_settings["storage"]["active_default_storage_type"]
            == payload["storage"]["active_default_storage_type"]
        )

        # now PATCH in a single notification property
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.patch(
            url,
            headers=auth_header,
            json=payload_single_notification_property,
        )
        assert response.status_code == 200

        # then we test that we can GET it
        auth_header = generate_auth_header([scopes.CONFIG_READ])
        response = api_client.get(
            url,
            headers=auth_header,
            params={"api_set": True},
        )
        assert response.status_code == 200
        response_settings = response.json()
        assert (
            response_settings["storage"]["active_default_storage_type"]
            == payload["storage"]["active_default_storage_type"]
        )
        assert (
            response_settings["notifications"]["notification_service_type"]
            == payload_single_notification_property["notifications"][
                "notification_service_type"
            ].upper()
        )


class TestDeleteApplicationConfig:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return urls.V1_URL_PREFIX + urls.CONFIG

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            "storage": {"active_default_storage_type": StorageType.s3.value},
            "notifications": {
                "notification_service_type": "TWILIO_TEXT",
                "send_request_completion_notification": True,
                "send_request_receipt_notification": True,
                "send_request_review_notification": True,
            },
            "execution": {
                "subject_identity_verification_required": True,
                "require_manual_request_approval": True,
            },
        }

    def test_reset_application_config(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        db: Session,
        payload,
    ):
        # first we PATCH in some settings
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.patch(
            url,
            headers=auth_header,
            json=payload,
        )
        assert response.status_code == 200

        # then we test that we can GET them
        auth_header = generate_auth_header([scopes.CONFIG_READ])
        response = api_client.get(
            url,
            headers=auth_header,
            params={"api_set": True},
        )
        assert response.status_code == 200
        response_settings = response.json()
        assert (
            response_settings["storage"]["active_default_storage_type"]
            == payload["storage"]["active_default_storage_type"]
        )

        # then we delete them
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.delete(
            url,
            headers=auth_header,
        )
        assert response.status_code == 200

        # then we ensure they are no longer returned
        auth_header = generate_auth_header([scopes.CONFIG_READ])
        response = api_client.get(
            url,
            headers=auth_header,
            params={"api_set": True},
        )
        assert response.status_code == 200
        response_settings = response.json()
        assert response_settings == {}

        # and cleared from the db
        db_settings = db.query(ApplicationConfig).first()
        # this should be empty
        assert db_settings.api_set == {}

    def test_reset_application_config_non_existing(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        db: Session,
    ):
        """
        Test that a DELETE works even if no 'api-set' settings have been set yet
        """
        # we ensure they are not returned
        auth_header = generate_auth_header([scopes.CONFIG_READ])
        response = api_client.get(
            url,
            headers=auth_header,
            params={"api_set": True},
        )
        assert response.status_code == 200
        response_settings = response.json()
        assert response_settings == {}

        # and nothing in the db
        db_settings = db.query(ApplicationConfig).first()
        # this should be empty
        assert db_settings.api_set == {}

        # actually run the delete
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.delete(
            url,
            headers=auth_header,
        )
        assert response.status_code == 200

        # we ensure they are still not returned
        auth_header = generate_auth_header([scopes.CONFIG_READ])
        response = api_client.get(
            url,
            headers=auth_header,
            params={"api_set": True},
        )
        assert response.status_code == 200
        response_settings = response.json()
        assert response_settings == {}

        # and still nothing in the db
        db_settings = db.query(ApplicationConfig).first()
        # this should be empty
        assert db_settings.api_set == {}

        # now actually delete the application config record
        db_settings.delete(db)
        # and ensure the delete call doesn't error
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.delete(
            url,
            headers=auth_header,
        )
        assert response.status_code == 200

        # and ensure the GET works but still returns nothing
        auth_header = generate_auth_header([scopes.CONFIG_READ])
        response = api_client.get(
            url,
            headers=auth_header,
            params={"api_set": True},
        )
        assert response.status_code == 200
        response_settings = response.json()
        assert response_settings == {}


class TestGetConnections:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return urls.V1_URL_PREFIX + urls.CONFIG

    def test_get_config(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
    ) -> None:
        auth_header = generate_auth_header(scopes=[scopes.CONFIG_READ])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == 200

        config = resp.json()
        assert "database" in config
        assert "password" not in config["database"]
        assert "redis" in config
        assert "password" not in config["redis"]
        assert "security" in config
        security_keys = set(config["security"].keys())
        assert (
            len(
                security_keys.difference(
                    set(
                        [
                            "cors_origins",
                            "encoding",
                            "oauth_access_token_expire_minutes",
                            "subject_request_download_link_ttl_seconds",
                        ]
                    )
                )
            )
            == 0
        )
