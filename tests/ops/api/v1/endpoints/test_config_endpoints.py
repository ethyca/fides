from __future__ import annotations

import copy
from typing import Any, Generator

import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fides.api.main import app
from fides.api.models.application_config import ApplicationConfig
from fides.api.oauth.roles import CONTRIBUTOR, OWNER, VIEWER
from fides.api.schemas.storage.storage import StorageType
from fides.api.util.cors_middleware_utils import (
    find_cors_middleware,
    update_cors_middleware,
)
from fides.common.api import scope_registry as scopes
from fides.common.api.v1 import urn_registry as urls


@pytest.fixture(scope="function")
def original_cors_middleware_origins() -> Generator:
    """
    Fixture to be run on any test that updates cors origins.
    Fixture teardown ensure cors origin middleware is reset to its original state.

    The fixture also yields the cors middleware original allow_origins values.
    """

    original_cors_middleware = find_cors_middleware(app)

    assert original_cors_middleware is not None

    yield original_cors_middleware.kwargs["allow_origins"]

    # on teardown - find the new cors middleware, remove it, and add back in the original
    update_cors_middleware(
        app,
        original_cors_middleware.kwargs["allow_origins"],
        original_cors_middleware.kwargs.get("allow_origin_regex"),
    )


class TestPatchApplicationConfig:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return urls.V1_URL_PREFIX + urls.CONFIG

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            "storage": {"active_default_storage_type": StorageType.s3.value},
            "notifications": {
                "notification_service_type": "twilio_text",
                "send_request_completion_notification": True,
                "send_request_receipt_notification": True,
                "send_request_review_notification": True,
            },
            "execution": {
                "subject_identity_verification_required": True,
                "require_manual_request_approval": True,
            },
            "security": {
                "cors_origins": [
                    "http://acme1.example.com/",
                    "http://acme2.example.com",
                    "http://acme3.example.com",
                ]
            },
            "admin_ui": {"enabled": True, "url": "http://localhost:3000/"},
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

    def test_patch_application_config_viewer_role(
        self, api_client: TestClient, payload, url, generate_role_header
    ):
        auth_header = generate_role_header(roles=[VIEWER])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_patch_application_config_contributor_role(
        self, api_client: TestClient, payload, url, generate_role_header
    ):
        auth_header = generate_role_header(roles=[CONTRIBUTOR])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

    def test_patch_application_config_admin_role(
        self, api_client: TestClient, payload, url, generate_role_header
    ):
        auth_header = generate_role_header(roles=[OWNER])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

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

        admin_ui_payload = copy.deepcopy(payload["admin_ui"])
        admin_ui_payload["url"] = admin_ui_payload["url"].rstrip("/")
        assert (
            response_settings["admin_ui"] == admin_ui_payload
        )  # Verify trailing slash stripped
        db_settings = db.query(ApplicationConfig).first()
        assert db_settings.api_set["storage"] == payload["storage"]
        assert db_settings.api_set["execution"] == payload["execution"]
        assert db_settings.api_set["notifications"] == payload["notifications"]
        assert db_settings.api_set["admin_ui"] == admin_ui_payload

        # Security payload - cors origins had their trailing slashes removed
        security_payload = copy.deepcopy(payload["security"])
        security_payload["cors_origins"] = [
            url.rstrip("/") for url in security_payload["cors_origins"]
        ]
        assert db_settings.api_set["security"] == security_payload

        response = api_client.get(
            urls.V1_URL_PREFIX + urls.CONFIG,
            headers=generate_auth_header([scopes.CONFIG_READ]),
            params={"api_set": True},
        )
        # No trailing slash on url
        assert response.json()["admin_ui"] == {
            "enabled": True,
            "url": "http://localhost:3000",
        }

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
        assert db_settings.api_set["security"] == security_payload

        # try PATCHing multiple properties in the same nested object
        updated_payload = {
            "execution": {"subject_identity_verification_required": False},
            "notifications": {
                "notification_service_type": "mailgun",
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
            response_settings["notifications"]["notification_service_type"] == "mailgun"
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
        assert db_settings.api_set["security"] == security_payload

        db.refresh(db_settings)
        # ensure property was updated on backend
        assert db_settings.api_set["storage"]["active_default_storage_type"] == "local"
        assert (
            db_settings.api_set["execution"]["subject_identity_verification_required"]
            is False
        )
        assert (
            db_settings.api_set["notifications"]["notification_service_type"]
            == "mailgun"
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
        assert db_settings.api_set["security"] == security_payload

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

    def test_patch_application_config_updates_cors_domains_in_middleware(
        self,
        api_client: TestClient,
        generate_auth_header,
        original_cors_middleware_origins,
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

        current_cors_middleware = find_cors_middleware(api_client.app)

        requested_origins = {
            url.rstrip("/") for url in set(payload["security"]["cors_origins"])
        }
        assert set(
            current_cors_middleware.kwargs["allow_origins"]
        ) == requested_origins.union(set(original_cors_middleware_origins))

        # now ensure that the middleware update was effective by trying
        # some sample requests with different origins

        # first, try with an original allowed origin, which should still be accepted
        assert len(original_cors_middleware_origins)
        headers = {
            **auth_header,
            "Origin": original_cors_middleware_origins[0],
            "Access-Control-Request-Method": "PATCH",
        }

        response = api_client.options(url, headers=headers)
        assert response.status_code == 200

        # now try with a new allowed origin, which should also be accepted
        headers = {
            **auth_header,
            "Origin": "http://acme1.example.com",
            "Access-Control-Request-Method": "PATCH",
        }
        response = api_client.options(url, headers=headers)
        assert response.status_code == 200

    def test_patch_application_config_updates_cors_domains_rejects_invalid_urls(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        db: Session,
    ):
        """
        Ensure invalid URL values for cors origin domains are rejected by API.
        """

        payload = {"security": {"cors_origins": ["*"]}}
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.patch(
            url,
            headers=auth_header,
            json=payload,
        )
        assert response.status_code == 422

        payload = {"security": {"cors_origins": ["test.com"]}}
        response = api_client.patch(
            url,
            headers=auth_header,
            json=payload,
        )
        assert response.status_code == 422

        payload = {"security": {"cors_origins": ["test"]}}
        response = api_client.patch(
            url,
            headers=auth_header,
            json=payload,
        )
        assert response.status_code == 422

        payload = {"security": {"cors_origins": ["http://test.com/path"]}}
        response = api_client.patch(
            url,
            headers=auth_header,
            json=payload,
        )
        assert response.status_code == 422

        payload = {"security": {"cors_origins": ["http://test.com/123/456"]}}
        response = api_client.patch(
            url,
            headers=auth_header,
            json=payload,
        )
        assert response.status_code == 422

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


class TestPutApplicationConfig:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return urls.V1_URL_PREFIX + urls.CONFIG

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            "storage": {"active_default_storage_type": StorageType.s3.value},
            "notifications": {
                "notification_service_type": "twilio_text",
                "send_request_completion_notification": True,
                "send_request_receipt_notification": True,
                "send_request_review_notification": True,
            },
            "execution": {
                "subject_identity_verification_required": True,
                "require_manual_request_approval": True,
            },
            "security": {
                "cors_origins": [
                    "http://acme1.example.com",
                    "http://acme2.example.com",
                    "http://acme3.example.com",
                ]
            },
        }

    def test_put_application_config_unauthenticated(
        self, api_client: TestClient, payload, url
    ):
        response = api_client.put(url, headers={}, json=payload)
        assert 401 == response.status_code

    def test_put_application_config_wrong_scope(
        self, api_client: TestClient, payload, url, generate_auth_header
    ):
        auth_header = generate_auth_header([scopes.CONFIG_READ])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_put_application_config_viewer_role(
        self, api_client: TestClient, payload, url, generate_role_header
    ):
        auth_header = generate_role_header(roles=[VIEWER])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_put_application_config_contributor_role(
        self, api_client: TestClient, payload, url, generate_role_header
    ):
        auth_header = generate_role_header(roles=[CONTRIBUTOR])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

    def test_put_application_config_admin_role(
        self, api_client: TestClient, payload, url, generate_role_header
    ):
        auth_header = generate_role_header(roles=[OWNER])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

    def test_put_application_config_with_invalid_key(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        payload: dict[str, Any],
    ):
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.put(
            url, headers=auth_header, json={"storage": {"bad_key": "s3"}}
        )
        assert response.status_code == 422

        response = api_client.put(
            url,
            headers=auth_header,
            json={"bad_key": {"active_default_storage_type": "s3"}},
        )
        assert response.status_code == 422

        # now test payload with both a good key and a bad key - should be rejected
        payload["bad_key"] = "12345"
        response = api_client.put(url, headers=auth_header, json=payload)
        assert response.status_code == 422

        # and a nested bad key
        payload.pop("bad_key")
        payload["storage"]["bad_key"] = "12345"
        response = api_client.put(url, headers=auth_header, json=payload)
        assert response.status_code == 422

    def test_put_application_config_with_invalid_value(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.put(
            url,
            headers=auth_header,
            json={"storage": {"active_default_storage_type": 33}},
        )
        assert response.status_code == 422

        response = api_client.put(
            url,
            headers=auth_header,
            json={"storage": {"active_default_storage_type": "fake_storage_type"}},
        )
        assert response.status_code == 422

        # gcs is valid storage type but not allowed currently
        # as an `active_default_storage_type``
        response = api_client.put(
            url,
            headers=auth_header,
            json={"storage": {"active_default_storage_type": StorageType.gcs.value}},
        )
        assert response.status_code == 422

    def test_put_application_config_empty_body(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
    ):
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.put(
            url,
            headers=auth_header,
            json={},
        )
        assert response.status_code == 422

        response = api_client.put(
            url,
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_put_application_config(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        payload,
        db: Session,
    ):
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.put(
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
        assert db_settings.api_set["security"] == payload["security"]

        # try PUTing a single property
        updated_payload = {"storage": {"active_default_storage_type": "local"}}
        response = api_client.put(
            url,
            headers=auth_header,
            json=updated_payload,
        )
        assert response.status_code == 200
        response_settings = response.json()
        assert response_settings["storage"]["active_default_storage_type"] == "local"
        # ensure other properties were nulled
        assert response_settings.get("execution") is None
        assert response_settings.get("notifications") is None
        db.refresh(db_settings)
        # ensure property was updated on backend
        assert db_settings.api_set["storage"]["active_default_storage_type"] == "local"
        # but other properties are no longer present
        assert db_settings.api_set.get("execution") is None
        assert db_settings.api_set.get("notifications") is None
        assert db_settings.api_set.get("security") is None

        # try PUTing multiple properties in the same nested object
        updated_payload = {
            "execution": {"subject_identity_verification_required": False},
            "notifications": {
                "notification_service_type": "mailgun",
                "send_request_completion_notification": False,
            },
        }
        response = api_client.put(
            url,
            headers=auth_header,
            json=updated_payload,
        )
        assert response.status_code == 200
        response_settings = response.json()
        assert (
            response_settings["execution"]["subject_identity_verification_required"]
            is False
        )
        assert (
            response_settings["notifications"]["notification_service_type"] == "mailgun"
        )
        assert (
            response_settings["notifications"]["send_request_completion_notification"]
            is False
        )
        # ensure other properties are no longer present
        assert response_settings.get("storage") is None
        assert (
            response_settings["notifications"].get("send_request_receipt_notification")
            is None
        )
        assert response_settings.get("security") is None

        db.refresh(db_settings)
        # ensure specified properties were updated on backend
        assert (
            db_settings.api_set["execution"]["subject_identity_verification_required"]
            is False
        )
        assert (
            db_settings.api_set["notifications"]["notification_service_type"]
            == "mailgun"
        )
        assert (
            db_settings.api_set["notifications"]["send_request_completion_notification"]
            is False
        )
        # ensure other properties are no longer present
        assert db_settings.api_set.get("storage") == None
        assert (
            db_settings.api_set["notifications"].get(
                "send_request_receipt_notification"
            )
            is None
        )
        assert db_settings.api_set.get("security") is None

    def test_put_application_config_updates_cors_domains_in_middleware(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        payload,
        original_cors_middleware_origins,
    ):
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        new_cors_origins = payload["security"]["cors_origins"]

        # try with a new allowed origin, which should not be accepted yet
        # since we have not made the config update yet
        headers = {
            **auth_header,
            "Origin": new_cors_origins[0],
            "Access-Control-Request-Method": "PUT",
        }
        response = api_client.options(url, headers=headers)
        assert response.status_code == 400
        assert response.text == "Disallowed CORS origin"

        # if we set cors origins values via API, ensure that those are the
        # `allow_origins` values on the active cors middleware
        response = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert response.status_code == 200

        current_cors_middleware = find_cors_middleware(api_client.app)

        assert set(current_cors_middleware.kwargs["allow_origins"]) == set(
            new_cors_origins
        ).union(set(original_cors_middleware_origins))

        # now ensure that the middleware update was effective by trying
        # some sample requests with different origins

        # first, try with an original allowed origin, which should still be accepted
        assert len(original_cors_middleware_origins)
        headers = {
            **auth_header,
            "Origin": original_cors_middleware_origins[0],
            "Access-Control-Request-Method": "PUT",
        }
        response = api_client.options(url, headers=headers)
        assert response.status_code == 200

        # now try with a new allowed origin, which should also be accepted
        headers = {
            **auth_header,
            "Origin": new_cors_origins[0],
            "Access-Control-Request-Method": "PUT",
        }
        response = api_client.options(url, headers=headers)
        assert response.status_code == 200

        # but ensure that an unrelated origin is still not allowed
        headers = {
            **auth_header,
            "Origin": "https://fakesite.com",
            "Access-Control-Request-Method": "PUT",
        }
        response = api_client.options(url, headers=headers)
        assert response.status_code == 400
        assert response.text == "Disallowed CORS origin"

        # but then ensure that we can revert back to the original values
        # by PUTing a config that does not have cors origins specified
        payload.pop("security")  # remove cors origins from PUT payload
        response = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert response.status_code == 200

        current_cors_middleware = find_cors_middleware(api_client.app)
        assert set(current_cors_middleware.kwargs["allow_origins"]) == set(
            original_cors_middleware_origins
        )  # assert our cors middleware has been reset to original values

        # now ensure that the middleware update was effective by trying
        # some sample requests with different origins

        # first, try with an original allowed origin, which should still be accepted
        assert len(original_cors_middleware_origins)
        headers = {
            **auth_header,
            "Origin": original_cors_middleware_origins[0],
            "Access-Control-Request-Method": "PUT",
        }
        response = api_client.options(url, headers=headers)
        assert response.status_code == 200

        # now try with a "new" allowed origin, which should no longer be accepted
        headers = {
            **auth_header,
            "Origin": new_cors_origins[0],
            "Access-Control-Request-Method": "PUT",
        }
        response = api_client.options(url, headers=headers)
        assert response.status_code == 400
        assert response.text == "Disallowed CORS origin"


class TestGetApplicationConfigApiSet:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return urls.V1_URL_PREFIX + urls.CONFIG

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            "storage": {"active_default_storage_type": StorageType.s3.value},
            "security": {
                "cors_origins": [
                    "http://acme1.example.com",
                    "http://acme2.example.com",
                    "http://acme3.example.com",
                ]
            },
        }

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
        assert response_settings["security"] == payload["security"]

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
            ]
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
                "notification_service_type": "twilio_text",
                "send_request_completion_notification": True,
                "send_request_receipt_notification": True,
                "send_request_review_notification": True,
            },
            "execution": {
                "subject_identity_verification_required": True,
                "require_manual_request_approval": True,
            },
            "security": {
                "cors_origins": [
                    "http://acme1.example.com",
                    "http://acme2.example.com",
                    "http://acme3.example.com",
                ]
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

    def test_reset_removes_all_cors_domain_from_middleware(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        db: Session,
        payload,
    ):
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.patch(
            url,
            headers=auth_header,
            json=payload,
        )
        assert response.status_code == 200

        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.delete(
            url,
            headers=auth_header,
        )
        assert response.status_code == 200
        # Check the app config direcitly to make sure it's reset and
        # by proxy check that the CORS domains are reset.
        # The middleware isn't checked directly because it's
        # possible that the config set will still have some
        # domains and when the `api_set` is reset the middleware
        # will still have the `config_set` domains loaded in.
        assert ApplicationConfig.get_api_set(db) == {}


class TestGetConfig:
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

        # effectively hardcode our allow list here in our tests to flag any additions to the allowlist!
        # allowlist additions should be made with care, and _need_ to be reviewed by the
        # Ethyca security team
        allowed_top_level_config_keys = {
            "admin_ui",
            "user",
            "logging",
            "notifications",
            "security",
            "execution",
            "storage",
            "consent",
        }

        for key in config.keys():
            assert (
                key in allowed_top_level_config_keys
            ), "Unexpected config API change, please review with Ethyca security team"

        assert "security" in config
        assert "user" in config
        assert "logging" in config
        assert "notifications" in config

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
                            "cors_origin_regex",
                        ]
                    )
                )
            )
            == 0
        ), "Unexpected config API change, please review with Ethyca security team"

        user_keys = set(config["user"].keys())
        assert (
            len(
                user_keys.difference(
                    set(
                        [
                            "analytics_opt_out",
                        ]
                    )
                )
            )
            == 0
        ), "Unexpected config API change, please review with Ethyca security team"

        logging_keys = set(config["logging"].keys())
        assert (
            len(
                logging_keys.difference(
                    set(
                        [
                            "level",
                        ]
                    )
                )
            )
            == 0
        ), "Unexpected config API change, please review with Ethyca security team"

        notifications_keys = set(config["notifications"].keys())
        assert (
            len(
                notifications_keys.difference(
                    set(
                        [
                            "send_request_completion_notification",
                            "send_request_receipt_notification",
                            "send_request_review_notification",
                            "notification_service_type",
                            "enable_property_specific_messaging",
                        ]
                    )
                )
            )
            == 0
        ), "Unexpected config API change, please review with Ethyca security team"

        execution_keys = set(config["execution"].keys())
        assert (
            len(
                execution_keys.difference(
                    set(
                        [
                            "task_retry_count",
                            "task_retry_delay",
                            "task_retry_backoff",
                            "require_manual_request_approval",
                            "subject_identity_verification_required",
                        ]
                    )
                )
            )
            == 0
        ), "Unexpected config API change, please review with Ethyca security team"

        if "storage" in config:  # storage not necessarily in config in test runtime
            storage_keys = set(config["storage"].keys())
            assert (
                len(
                    storage_keys.difference(
                        set(
                            [
                                "active_default_storage_type",
                            ]
                        )
                    )
                )
                == 0
            ), "Unexpected config API change, please review with Ethyca security team"

        consent_keys = set(config["consent"].keys())
        assert (
            len(consent_keys.difference(set(["override_vendor_purposes"]))) == 0
        ), "Unexpected config API change, please review with Ethyca security team"

        execution_keys = set(config["admin_ui"].keys())
        assert (
            len(execution_keys.difference(set(["enabled", "url"]))) == 0
        ), "Unexpected config API change, please review with Ethyca security team"
