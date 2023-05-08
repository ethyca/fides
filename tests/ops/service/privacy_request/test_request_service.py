from datetime import datetime

import pytest
from httpx import HTTPStatusError

from fides.api.ctl.database.seed import create_or_update_parent_user
from fides.api.ops.api.v1.urn_registry import LOGIN, V1_URL_PREFIX
from fides.api.ops.cryptography.cryptographic_util import str_to_b64_str
from fides.api.ops.models.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fides.api.ops.service.privacy_request.request_service import (
    build_required_privacy_request_kwargs,
    poll_server_for_completion,
)
from fides.core.config import CONFIG


@pytest.fixture
def parent_user_config():
    original_user = CONFIG.security.parent_server_username
    original_password = CONFIG.security.parent_server_password
    CONFIG.security.parent_server_username = "parent_user"
    CONFIG.security.parent_server_password = "Apassword1!"
    yield
    CONFIG.security.parent_server_username = original_user
    CONFIG.security.parent_server_password = original_password


@pytest.mark.parametrize("status", ["complete", "denied", "canceled", "error"])
@pytest.mark.usefixtures("parent_user_config")
async def test_poll_server_for_completion(status, async_api_client, db, policy):
    create_or_update_parent_user()

    pr = PrivacyRequest.create(
        db=db,
        data={
            "requested_at": None,
            "policy_id": policy.id,
            "status": status,
        },
    )

    login_url = f"{V1_URL_PREFIX}{LOGIN}"
    body = {
        "username": CONFIG.security.parent_server_username,
        "password": str_to_b64_str(CONFIG.security.parent_server_password),
    }

    login_response = await async_api_client.post(login_url, json=body)

    response = await poll_server_for_completion(
        privacy_request_id=pr.id,
        server_url="http://0.0.0.0:8080",
        token=login_response.json()["token_data"]["access_token"],
        client=async_api_client,
        poll_interval_seconds=1,
    )

    assert response.status == status


@pytest.mark.usefixtures("parent_user_config")
async def test_poll_server_for_completion_timeout(async_api_client, db, policy):
    create_or_update_parent_user()

    pr = PrivacyRequest.create(
        db=db,
        data={
            "requested_at": None,
            "policy_id": policy.id,
            "status": "pending",
        },
    )

    login_url = f"{V1_URL_PREFIX}{LOGIN}"
    body = {
        "username": CONFIG.security.parent_server_username,
        "password": str_to_b64_str(CONFIG.security.parent_server_password),
    }

    login_response = await async_api_client.post(login_url, json=body)

    with pytest.raises(TimeoutError):
        await poll_server_for_completion(
            privacy_request_id=pr.id,
            server_url="http://0.0.0.0:8080",
            token=login_response.json()["token_data"]["access_token"],
            client=async_api_client,
            poll_interval_seconds=1,
            timeout_seconds=2,
        )


@pytest.mark.usefixtures("parent_user_config")
async def test_poll_server_for_completion_non_200(async_api_client, db, policy):
    create_or_update_parent_user()

    pr = PrivacyRequest.create(
        db=db,
        data={
            "requested_at": None,
            "policy_id": policy.id,
            "status": "complete",
        },
    )

    with pytest.raises(HTTPStatusError):
        await poll_server_for_completion(
            privacy_request_id=pr.id,
            server_url="http://0.0.0.0:8080",
            token="somebadtoken",
            client=async_api_client,
            poll_interval_seconds=1,
        )


class TestBuildPrivacyRequestRequiredKwargs:
    def test_build_required_privacy_request_kwargs_authenticated(self):
        resp = build_required_privacy_request_kwargs(
            requested_at=datetime.now(),
            policy_id="test_id",
            verification_required=True,
            authenticated=True,
        )
        assert resp["requested_at"] is not None
        assert resp["policy_id"] == "test_id"
        assert resp["status"] == PrivacyRequestStatus.pending

    def test_build_required_privacy_request_kwargs_not_authenticated(self):
        resp = build_required_privacy_request_kwargs(
            requested_at=datetime.now(),
            policy_id="test_id",
            verification_required=True,
            authenticated=False,
        )
        assert resp["requested_at"] is not None
        assert resp["policy_id"] == "test_id"
        assert resp["status"] == PrivacyRequestStatus.identity_unverified

    def test_build_required_privacy_request_kwargs_identity_verification_not_required(
        self,
    ):
        resp = build_required_privacy_request_kwargs(
            requested_at=datetime.now(),
            policy_id="test_id",
            verification_required=False,
            authenticated=False,
        )
        assert resp["requested_at"] is not None
        assert resp["policy_id"] == "test_id"
        assert resp["status"] == PrivacyRequestStatus.pending
