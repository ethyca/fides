import json
from typing import Dict

import pytest

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.pre_approval_webhook import PreApprovalWebhook
from fides.common.api.scope_registry import (
    WEBHOOK_CREATE_OR_UPDATE,
    WEBHOOK_DELETE,
    WEBHOOK_READ,
)
from fides.common.api.v1.urn_registry import (
    V1_URL_PREFIX,
    WEBHOOK_PRE_APPROVAL,
    WEBHOOK_PRE_APPROVAL_DETAIL,
)
from tests.ops.api.v1.endpoints.privacy_request.test_privacy_request_endpoints import stringify_date


def embedded_http_connection_config(connection_config: ConnectionConfig) -> Dict:
    """Helper to reduce clutter - a lot of the tests below assert the entire response body, which includes the
    https connection config"""
    return {
        "name": connection_config.name,
        "key": connection_config.key,
        "connection_type": "https",
        "access": connection_config.access.value,
        "created_at": stringify_date(connection_config.created_at),
        "updated_at": stringify_date(connection_config.updated_at),
        "last_test_timestamp": None,
        "last_test_succeeded": None,
        "disabled": False,
        "description": None,
        "saas_config": None,
        "secrets": None,
        "authorized": False,
        "enabled_actions": None,
    }


class TestGetPreApprovalWebhooks:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + WEBHOOK_PRE_APPROVAL

    def test_get_pre_approval_webhooks_unauthenticated(self, url, api_client):
        resp = api_client.get(url)
        assert resp.status_code == 401

    def test_get_pre_approval_webhooks_wrong_scope(
        self, url, api_client, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[WEBHOOK_DELETE])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

    def test_get_pre_approval_webhooks(
        self,
        url,
        db,
        api_client,
        generate_auth_header,
        pre_approval_webhooks,
        https_connection_config,
    ):
        auth_header = generate_auth_header(scopes=[WEBHOOK_READ])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == 200
        body = json.loads(resp.text)

        assert body == {
            "items": [
                {
                    "key": "pre_approval_webhook",
                    "name": pre_approval_webhooks[0].name,
                    "connection_config": embedded_http_connection_config(
                        https_connection_config
                    ),
                },
                {
                    "key": "pre_approval_webhook_2",
                    "name": pre_approval_webhooks[1].name,
                    "connection_config": embedded_http_connection_config(
                        https_connection_config
                    ),
                },
            ],
            "total": 2,
            "page": 1,
            "pages": 1,
            "size": 50,
        }


class TestGetPreApprovalWebhooksDetail:
    @pytest.fixture(scope="function")
    def url(self, pre_approval_webhooks) -> str:
        return V1_URL_PREFIX + WEBHOOK_PRE_APPROVAL_DETAIL.format(
            webhook_key=pre_approval_webhooks[0].key
        )

    def test_get_pre_approval_webhook_detail_unauthenticated(self, url, api_client):
        resp = api_client.get(url)
        assert resp.status_code == 401

    def test_get_pre_approval_webhook_detail_wrong_scope(
        self, url, api_client, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[WEBHOOK_DELETE])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

    def test_get_pre_approval_webhook_detail(
        self,
        url,
        db,
        api_client,
        generate_auth_header,
        pre_approval_webhooks,
        https_connection_config,
    ):
        auth_header = generate_auth_header(scopes=[WEBHOOK_READ])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == 200
        body = json.loads(resp.text)

        assert body == {
            "key": "pre_approval_webhook",
            "name": pre_approval_webhooks[0].name,
            "connection_config": embedded_http_connection_config(
                https_connection_config
            ),
        }


class TestPutPreApprovalWebhooks:
    @pytest.fixture(scope="function")
    def valid_webhook_request(self, https_connection_config) -> Dict:
        return {
            "connection_config_key": https_connection_config.key,
            "name": "My webhook",
            "key": "my_webhook",
        }

    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + WEBHOOK_PRE_APPROVAL

    def test_put_pre_approval_webhooks_unauthenticated(self, url, api_client):
        resp = api_client.put(url)
        assert resp.status_code == 401

    def test_put_pre_approval_webhooks_wrong_scope(
        self, url, api_client, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[WEBHOOK_READ])
        resp = api_client.put(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

    def test_invalid_connection_config(
        self, db, url, api_client, generate_auth_header, valid_webhook_request
    ):
        invalid_connection_config_body = {
            "connection_config_key": "unknown_connection_key",
            "name": "my_pre_approval_webhook",
        }

        auth_header = generate_auth_header(scopes=[WEBHOOK_CREATE_OR_UPDATE])
        resp = api_client.put(
            url,
            headers=auth_header,
            json=[valid_webhook_request, invalid_connection_config_body],
        )

        assert resp.status_code == 404
        body = json.loads(resp.text)
        assert (
            body["detail"]
            == "No connection configuration found with key 'unknown_connection_key'."
        )
        assert db.query(PreApprovalWebhook).count() == 0  # All must succeed or fail

    def test_put_pre_approval_webhooks_duplicate_keys(
        self,
        db,
        url,
        api_client,
        generate_auth_header,
        valid_webhook_request,
        https_connection_config,
    ):
        auth_header = generate_auth_header(scopes=[WEBHOOK_CREATE_OR_UPDATE])
        resp = api_client.put(
            url,
            headers=auth_header,
            json=[valid_webhook_request, valid_webhook_request],
        )
        assert resp.status_code == 400
        body = json.loads(resp.text)
        assert (
            body["detail"]
            == "Check request body: there are multiple webhooks whose keys or names resolve to the same value."
        )

        name_only = {
            "connection_config_key": https_connection_config.key,
            "name": "My webhook",
        }

        resp = api_client.put(
            url, headers=auth_header, json=[valid_webhook_request, name_only]
        )
        assert resp.status_code == 400
        body = json.loads(resp.text)
        assert (
            body["detail"]
            == "Check request body: there are multiple webhooks whose keys or names resolve to the same value."
        )
        assert db.query(PreApprovalWebhook).count() == 0  # All must succeed or fail

    def test_put_pre_approval_webhooks_duplicate_names(
        self,
        db,
        url,
        api_client,
        generate_auth_header,
        valid_webhook_request,
        https_connection_config,
    ):
        second_payload = valid_webhook_request.copy()
        second_payload["key"] = "new_key"

        auth_header = generate_auth_header(scopes=[WEBHOOK_CREATE_OR_UPDATE])
        resp = api_client.put(
            url,
            headers=auth_header,
            json=[valid_webhook_request, valid_webhook_request],
        )
        assert resp.status_code == 400
        body = json.loads(resp.text)
        assert (
            body["detail"]
            == "Check request body: there are multiple webhooks whose keys or names resolve to the same value."
        )

    def test_create_multiple_pre_approval_webhooks(
        self,
        db,
        generate_auth_header,
        api_client,
        url,
        valid_webhook_request,
        https_connection_config,
    ):
        second_webhook_body = {
            "connection_config_key": https_connection_config.key,
            "name": "My New Pre-Approval Webhook",
        }
        auth_header = generate_auth_header(scopes=[WEBHOOK_CREATE_OR_UPDATE])
        resp = api_client.put(
            url,
            headers=auth_header,
            json=[valid_webhook_request, second_webhook_body],
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)
        assert len(body) == 2
        assert body == [
            {
                "key": "my_webhook",
                "name": "My webhook",
                "connection_config": embedded_http_connection_config(
                    https_connection_config
                ),
            },
            {
                "key": "my_new_pre_approval_webhook",
                "name": "My New Pre-Approval Webhook",
                "connection_config": embedded_http_connection_config(
                    https_connection_config
                ),
            },
        ]

        webhooks = PreApprovalWebhook.filter(
            db=db,
            conditions=(
                PreApprovalWebhook.key.in_(
                    ["my_webhook", "my_new_pre_approval_webhook"]
                )
            ),
        )

        assert webhooks.count() == 2
        for webhook in webhooks:
            webhook.delete(db=db)

    def test_update_webhooks_remove_webhook_from_request(
        self,
        db,
        generate_auth_header,
        api_client,
        url,
        pre_approval_webhooks,
        https_connection_config,
    ):
        auth_header = generate_auth_header(scopes=[WEBHOOK_CREATE_OR_UPDATE])

        # Only include one webhook
        request_body = [
            {
                "connection_config_key": https_connection_config.key,
                "name": pre_approval_webhooks[0].name,
                "key": pre_approval_webhooks[0].key,
            },
        ]

        resp = api_client.put(
            url,
            headers=auth_header,
            json=request_body,
        )
        body = json.loads(resp.text)
        assert len(body) == 1  # Other webhook was removed
        assert body[0]["key"] == "pre_approval_webhook"


class TestPatchPreApprovalWebhook:
    """Test updating a single PreApprovalWebhook"""

    @pytest.fixture(scope="function")
    def url(self, pre_approval_webhooks) -> str:
        return V1_URL_PREFIX + WEBHOOK_PRE_APPROVAL_DETAIL.format(
            webhook_key=pre_approval_webhooks[0].key
        )

    def test_patch_pre_approval_webhook_unauthenticated(self, url, api_client):
        resp = api_client.patch(url)
        assert resp.status_code == 401

    def test_patch_pre_approval_webhook_wrong_scope(
        self, url, api_client, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[WEBHOOK_READ])
        resp = api_client.patch(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

    def test_patch_pre_approval_webhook_invalid_webhook_key(
        self, api_client, generate_auth_header
    ):
        invalid_url = V1_URL_PREFIX + WEBHOOK_PRE_APPROVAL_DETAIL.format(
            webhook_key="invalid_webhook_key"
        )
        request_body = {"name": "Renaming this webhook"}
        auth_header = generate_auth_header(scopes=[WEBHOOK_CREATE_OR_UPDATE])
        resp = api_client.patch(invalid_url, headers=auth_header, json=request_body)
        assert resp.status_code == 404

    def test_patch_pre_approval_webhook_nonexistent_connection_config_key(
        self, api_client, url, generate_auth_header
    ):
        request_body = {"connection_config_key": "nonexistent_key"}
        auth_header = generate_auth_header(scopes=[WEBHOOK_CREATE_OR_UPDATE])
        resp = api_client.patch(url, headers=auth_header, json=request_body)
        assert resp.status_code == 404

    def test_update_name_only(
        self,
        db,
        generate_auth_header,
        api_client,
        url,
        pre_approval_webhooks,
        https_connection_config,
    ):
        request_body = {"name": "Renaming this webhook"}
        auth_header = generate_auth_header(scopes=[WEBHOOK_CREATE_OR_UPDATE])
        resp = api_client.patch(url, headers=auth_header, json=request_body)
        assert resp.status_code == 200
        response_body = json.loads(resp.text)
        assert response_body == {
            "key": "pre_approval_webhook",
            "name": "Renaming this webhook",
            "connection_config": embedded_http_connection_config(
                https_connection_config
            ),
        }
        assert PreApprovalWebhook.filter(
            db=db, conditions=(PreApprovalWebhook.key == "pre_approval_webhook")
        ).first()


class TestDeletePreApprovalWebhook:
    @pytest.fixture(scope="function")
    def url(self, pre_approval_webhooks) -> str:
        return V1_URL_PREFIX + WEBHOOK_PRE_APPROVAL_DETAIL.format(
            webhook_key=pre_approval_webhooks[0].key
        )

    def test_delete_pre_approval_webhook(self, url, api_client):
        resp = api_client.delete(url)
        assert resp.status_code == 401

    def test_delete_pre_approval_webhook_detail_wrong_scope(
        self, url, api_client, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[WEBHOOK_READ])
        resp = api_client.delete(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

    def test_delete_pre_approval_webhook_detail(
        self,
        db,
        url,
        api_client,
        generate_auth_header,
        pre_approval_webhooks,
    ):
        auth_header = generate_auth_header(scopes=[WEBHOOK_DELETE])
        resp = api_client.delete(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        all_webhooks = db.query(PreApprovalWebhook)
        assert all_webhooks.count() == 1
        assert (
            all_webhooks[0].key == pre_approval_webhooks[1].key
        )  # should keep the other configured webhook
