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
from fides.common.api.v1.urn_registry import PRIVACY_REQUEST_FINALIZE, V1_URL_PREFIX
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
        auth_header = generate_auth_header(
            scopes=[PRIVACY_REQUEST_REVIEW],
        )
        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 200

        privacy_request_requires_manual_finalization.refresh_from_db(db=db)
        assert privacy_request_requires_manual_finalization.finalized_at is not None
        # This is an e2e test that actually hits the request_runner_service logic, which marks the request as complete
        assert (
            privacy_request_requires_manual_finalization.status
            == PrivacyRequestStatus.complete
        )
