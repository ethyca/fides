import json
from datetime import datetime
from unittest import mock

import pytest

from fides.api.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_ROLES,
)
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.oauth.jwt import generate_jwe
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.common.api.scope_registry import PRIVACY_REQUEST_READ, PRIVACY_REQUEST_REVIEW
from fides.common.api.v1.urn_registry import (
    PRIVACY_REQUEST_BULK_FINALIZE,
    PRIVACY_REQUEST_FINALIZE,
    V1_URL_PREFIX,
)
from fides.config import CONFIG


class TestFinalizePrivacyRequest:
    @pytest.fixture(scope="function")
    def url(self, privacy_request_requires_manual_finalization: PrivacyRequest) -> str:
        return V1_URL_PREFIX + PRIVACY_REQUEST_FINALIZE.format(
            privacy_request_id=privacy_request_requires_manual_finalization.id
        )

    def test_finalize_privacy_request_unauthenticated(self, api_client, url):
        response = api_client.post(url)
        assert response.status_code == 401

    def test_finalize_privacy_request_wrong_scope(
        self, api_client, url, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 403

    def test_finalize_privacy_request_wrong_status(
        self, api_client, generate_auth_header, privacy_request
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_FINALIZE.format(
            privacy_request_id=privacy_request.id
        )
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_REVIEW])
        response = api_client.post(url, headers=auth_header)
        from loguru import logger

        logger.info(response.json()["detail"])
        assert response.status_code == 400
        assert "Cannot manually finalize privacy request" in response.json()["detail"]

    def test_finalize_privacy_request(
        self,
        db,
        api_client,
        url,
        generate_auth_header,
        privacy_request_requires_manual_finalization,
        enable_erasure_request_finalization_required,
        user,
    ):
        payload = {
            JWE_PAYLOAD_ROLES: user.client.roles,
            JWE_PAYLOAD_CLIENT_ID: user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
        }
        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 200

        db.refresh(privacy_request_requires_manual_finalization)
        assert privacy_request_requires_manual_finalization.finalized_at is not None
        # This is an e2e test that actually hits the request_runner_service logic, which marks the request as complete
        assert (
            privacy_request_requires_manual_finalization.status
            == PrivacyRequestStatus.complete
        )
        print(user.id)
        assert privacy_request_requires_manual_finalization.finalized_by is not None
        assert privacy_request_requires_manual_finalization.finalized_by == user.id

    def test_finalize_privacy_request_root_user(
        self,
        db,
        api_client,
        url,
        privacy_request_requires_manual_finalization,
        enable_erasure_request_finalization_required,
        root_auth_header,
    ):
        response = api_client.post(url, headers=root_auth_header)
        assert response.status_code == 200
        db.refresh(privacy_request_requires_manual_finalization)

        assert privacy_request_requires_manual_finalization.finalized_at is not None
        # This is an e2e test that actually hits the request_runner_service logic, which marks the request as complete
        assert (
            privacy_request_requires_manual_finalization.status
            == PrivacyRequestStatus.complete
        )
        assert privacy_request_requires_manual_finalization.finalized_by is None


class TestBulkFinalizePrivacyRequest:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + PRIVACY_REQUEST_BULK_FINALIZE

    def test_bulk_finalize_privacy_request_unauthenticated(
        self, api_client, url, privacy_request_requires_manual_finalization
    ):
        response = api_client.post(
            url, json={"request_ids": [privacy_request_requires_manual_finalization.id]}
        )
        assert response.status_code == 401

    def test_bulk_finalize_privacy_request_wrong_scope(
        self,
        api_client,
        url,
        generate_auth_header,
        privacy_request_requires_manual_finalization,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url,
            json={"request_ids": [privacy_request_requires_manual_finalization.id]},
            headers=auth_header,
        )
        assert response.status_code == 403

    def test_bulk_finalize_privacy_request_wrong_status(
        self, api_client, url, generate_auth_header, privacy_request
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_REVIEW])
        response = api_client.post(
            url,
            json={"request_ids": [privacy_request.id]},
            headers=auth_header,
        )
        assert response.status_code == 200
        response_body = response.json()
        assert len(response_body["failed"]) == 1
        assert len(response_body["succeeded"]) == 0
        assert (
            "Cannot manually finalize privacy request"
            in response_body["failed"][0]["message"]
        )

    def test_bulk_finalize_privacy_request(
        self,
        db,
        api_client,
        url,
        generate_auth_header,
        privacy_request_requires_manual_finalization,
        enable_erasure_request_finalization_required,
        user,
    ):
        payload = {
            JWE_PAYLOAD_ROLES: user.client.roles,
            JWE_PAYLOAD_CLIENT_ID: user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
        }
        response = api_client.post(
            url,
            json={"request_ids": [privacy_request_requires_manual_finalization.id]},
            headers=auth_header,
        )
        assert response.status_code == 200

        response_body = response.json()
        assert len(response_body["succeeded"]) == 1
        assert len(response_body["failed"]) == 0
        assert (
            response_body["succeeded"][0]["id"]
            == privacy_request_requires_manual_finalization.id
        )

        db.refresh(privacy_request_requires_manual_finalization)
        assert privacy_request_requires_manual_finalization.finalized_at is not None
        # This is an e2e test that actually hits the request_runner_service logic, which marks the request as complete
        assert (
            privacy_request_requires_manual_finalization.status
            == PrivacyRequestStatus.complete
        )
        assert privacy_request_requires_manual_finalization.finalized_by == user.id

    def test_bulk_finalize_privacy_request_mixed_statuses(
        self,
        db,
        api_client,
        url,
        generate_auth_header,
        privacy_request_requires_manual_finalization,
        privacy_request,
        enable_erasure_request_finalization_required,
        user,
    ):
        """Test bulk finalize with a mix of valid and invalid privacy requests"""
        payload = {
            JWE_PAYLOAD_ROLES: user.client.roles,
            JWE_PAYLOAD_CLIENT_ID: user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
        }
        response = api_client.post(
            url,
            json={
                "request_ids": [
                    privacy_request_requires_manual_finalization.id,
                    privacy_request.id,  # This one is not in requires_manual_finalization status
                ]
            },
            headers=auth_header,
        )
        assert response.status_code == 200

        response_body = response.json()
        assert len(response_body["succeeded"]) == 1
        assert len(response_body["failed"]) == 1
        assert (
            response_body["succeeded"][0]["id"]
            == privacy_request_requires_manual_finalization.id
        )
        assert (
            "Cannot manually finalize privacy request"
            in response_body["failed"][0]["message"]
        )

        db.refresh(privacy_request_requires_manual_finalization)
        assert privacy_request_requires_manual_finalization.finalized_at is not None
        assert (
            privacy_request_requires_manual_finalization.status
            == PrivacyRequestStatus.complete
        )
        assert privacy_request_requires_manual_finalization.finalized_by == user.id

        # The other privacy request should not be affected
        db.refresh(privacy_request)
        assert privacy_request.finalized_at is None
        assert privacy_request.finalized_by is None

    def test_bulk_finalize_privacy_request_not_found(
        self,
        api_client,
        url,
        generate_auth_header,
        user,
    ):
        """Test bulk finalize with non-existent privacy request ID"""
        payload = {
            JWE_PAYLOAD_ROLES: user.client.roles,
            JWE_PAYLOAD_CLIENT_ID: user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
        }
        response = api_client.post(
            url,
            json={"request_ids": ["nonexistent_id"]},
            headers=auth_header,
        )
        assert response.status_code == 200

        response_body = response.json()
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1
        assert (
            "No privacy request found with id 'nonexistent_id'"
            == response_body["failed"][0]["message"]
        )
