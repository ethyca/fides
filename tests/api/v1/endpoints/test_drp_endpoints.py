from typing import Callable
from unittest import mock

import jwt
import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fidesops.api.v1.scope_registry import (
    POLICY_READ,
    PRIVACY_REQUEST_READ,
    PRIVACY_REQUEST_REVIEW,
    STORAGE_CREATE_OR_UPDATE,
)
from fidesops.api.v1.urn_registry import (
    DRP_DATA_RIGHTS,
    DRP_EXERCISE,
    DRP_REVOKE,
    DRP_STATUS,
    V1_URL_PREFIX,
)
from fidesops.core.config import config
from fidesops.models.policy import DrpAction
from fidesops.models.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fidesops.schemas.privacy_request import PrivacyRequestDRPStatus
from fidesops.util.cache import get_drp_request_body_cache_key, get_identity_cache_key


class TestCreateDrpPrivacyRequest:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + DRP_EXERCISE

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_drp_privacy_request(
        self,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        policy_drp_action,
        cache,
    ):
        TEST_EMAIL = "test@example.com"
        TEST_PHONE_NUMBER = "+1 234 567 8910"
        identity = {
            "email": TEST_EMAIL,
            "phone_number": TEST_PHONE_NUMBER,
        }
        encoded_identity: str = jwt.encode(
            identity, config.security.drp_jwt_secret, algorithm="HS256"
        )
        data = {
            "meta": {"version": "0.5"},
            "regime": "ccpa",
            "exercise": [DrpAction.access.value],
            "identity": encoded_identity,
        }
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()
        assert response_data["status"] == "open"
        assert response_data["received_at"]
        assert response_data["request_id"]
        pr = PrivacyRequest.get(db=db, object_id=response_data["request_id"])

        # test appropriate data is cached
        meta_key = get_drp_request_body_cache_key(
            privacy_request_id=pr.id,
            identity_attribute="meta",
        )
        assert cache.get(meta_key) == "DrpMeta(version='0.5')"
        regime_key = get_drp_request_body_cache_key(
            privacy_request_id=pr.id,
            identity_attribute="regime",
        )
        assert cache.get(regime_key) == "ccpa"
        exercise_key = get_drp_request_body_cache_key(
            privacy_request_id=pr.id,
            identity_attribute="exercise",
        )
        assert cache.get(exercise_key) == "['access']"
        identity_key = get_drp_request_body_cache_key(
            privacy_request_id=pr.id,
            identity_attribute="identity",
        )
        assert (
            cache.get(identity_key)
            == "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJwaG9uZV9udW1iZXIiOiIrMSAyMzQgNTY3IDg5MTAifQ.kHV4ru6vxQR96Meae31oKIU7mMnTJgt1cnli6GLUBFk"
        )
        fidesops_identity_key = get_identity_cache_key(
            privacy_request_id=pr.id,
            identity_attribute="email",
        )
        assert cache.get(fidesops_identity_key) == identity["email"]
        persisted_identity = pr.get_persisted_identity()
        assert persisted_identity.email == TEST_EMAIL
        assert persisted_identity.phone_number == TEST_PHONE_NUMBER

        pr.delete(db=db)
        assert run_access_request_mock.called

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_drp_privacy_request_unsupported_identity_props(
        self,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        policy_drp_action,
        cache,
    ):

        identity = {"email": "test@example.com", "address": "something"}
        encoded_identity: str = jwt.encode(
            identity, config.security.drp_jwt_secret, algorithm="HS256"
        )
        data = {
            "meta": {"version": "0.5"},
            "regime": "ccpa",
            "exercise": [DrpAction.access.value],
            "identity": encoded_identity,
        }
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()
        assert response_data["status"] == "open"
        assert response_data["received_at"]
        assert response_data["request_id"]
        pr = PrivacyRequest.get(db=db, object_id=response_data["request_id"])

        # test appropriate data is cached
        meta_key = get_drp_request_body_cache_key(
            privacy_request_id=pr.id,
            identity_attribute="meta",
        )
        assert cache.get(meta_key) == "DrpMeta(version='0.5')"
        regime_key = get_drp_request_body_cache_key(
            privacy_request_id=pr.id,
            identity_attribute="regime",
        )
        assert cache.get(regime_key) == "ccpa"
        exercise_key = get_drp_request_body_cache_key(
            privacy_request_id=pr.id,
            identity_attribute="exercise",
        )
        assert cache.get(exercise_key) == "['access']"
        identity_key = get_drp_request_body_cache_key(
            privacy_request_id=pr.id,
            identity_attribute="identity",
        )
        assert (
            cache.get(identity_key)
            == "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJhZGRyZXNzIjoic29tZXRoaW5nIn0.VhHzwTNoTjuny7lSebD6_hc0SU8kEZDr3YegONMMfmY"
        )
        fidesops_identity_key = get_identity_cache_key(
            privacy_request_id=pr.id,
            identity_attribute="email",
        )
        assert cache.get(fidesops_identity_key) == identity["email"]
        fidesops_identity_key_address = get_identity_cache_key(
            privacy_request_id=pr.id,
            identity_attribute="address",
        )
        assert cache.get(fidesops_identity_key_address) is None
        pr.delete(db=db)
        assert run_access_request_mock.called

    def test_create_drp_privacy_request_no_jwt(
        self,
        url,
        db,
        api_client: TestClient,
        policy_drp_action,
    ):

        original_secret = config.security.drp_jwt_secret
        config.security.drp_jwt_secret = None
        identity = {"email": "test@example.com"}
        encoded_identity: str = jwt.encode(identity, "secret", algorithm="HS256")
        data = {
            "meta": {"version": "0.5"},
            "regime": "ccpa",
            "exercise": [DrpAction.access.value],
            "identity": encoded_identity,
        }
        resp = api_client.post(url, json=data)
        assert resp.status_code == 500
        config.security.drp_jwt_secret = original_secret

    def test_create_drp_privacy_request_no_exercise(
        self,
        url,
        db,
        api_client: TestClient,
        policy_drp_action,
    ):

        identity = {"email": "test@example.com"}
        encoded_identity: str = jwt.encode(
            identity, config.security.drp_jwt_secret, algorithm="HS256"
        )
        data = {
            "meta": {"version": "0.5"},
            "regime": "ccpa",
            "exercise": None,
            "identity": encoded_identity,
        }
        resp = api_client.post(url, json=data)
        assert resp.status_code == 422

    def test_create_drp_privacy_request_invalid_exercise(
        self,
        url,
        db,
        api_client: TestClient,
        policy_drp_action,
    ):

        identity = {"email": "test@example.com"}
        encoded_identity: str = jwt.encode(
            identity, config.security.drp_jwt_secret, algorithm="HS256"
        )
        data = {
            "meta": {"version": "0.5"},
            "regime": "ccpa",
            "exercise": [DrpAction.access.value, DrpAction.deletion.value],
            "identity": encoded_identity,
        }
        resp = api_client.post(url, json=data)
        assert resp.status_code == 422

    def test_create_drp_privacy_request_no_associated_policy(
        self,
        url,
        db,
        api_client: TestClient,
        policy,
    ):

        identity = {"email": "test@example.com"}
        encoded_identity: str = jwt.encode(
            identity, config.security.drp_jwt_secret, algorithm="HS256"
        )
        data = {
            "meta": {"version": "0.5"},
            "regime": "ccpa",
            "exercise": [DrpAction.access.value],
            "identity": encoded_identity,
        }
        resp = api_client.post(url, json=data)
        assert resp.status_code == 404


class TestGetPrivacyRequestDRP:
    """
    Tests for the endpoint retrieving privacy requests specific to the DRP.
    """

    @pytest.fixture(scope="function")
    def url_for_privacy_request(
        self,
        privacy_request: PrivacyRequest,
    ) -> str:
        return V1_URL_PREFIX + DRP_STATUS + f"?request_id={privacy_request.id}"

    @pytest.fixture(scope="function")
    def url_for_privacy_request_with_drp_action(
        self,
        privacy_request_with_drp_action: PrivacyRequest,
    ) -> str:
        return (
            V1_URL_PREFIX
            + DRP_STATUS
            + f"?request_id={privacy_request_with_drp_action.id}"
        )

    def test_get_privacy_requests_unauthenticated(
        self,
        api_client: TestClient,
        url_for_privacy_request: str,
    ):
        response = api_client.get(
            url_for_privacy_request,
            headers={},
        )
        assert 401 == response.status_code

    def test_get_privacy_requests_wrong_scope(
        self,
        api_client: TestClient,
        generate_auth_header: Callable,
        url_for_privacy_request: str,
    ):
        auth_header = generate_auth_header(scopes=[STORAGE_CREATE_OR_UPDATE])
        response = api_client.get(
            url_for_privacy_request,
            headers=auth_header,
        )
        assert 403 == response.status_code

    def test_get_non_drp_privacy_request(
        self,
        api_client: TestClient,
        generate_auth_header: Callable,
        url_for_privacy_request: str,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            url_for_privacy_request,
            headers=auth_header,
        )
        assert 404 == response.status_code
        privacy_request_id = url_for_privacy_request.split("=")[-1]
        assert (
            response.json()["detail"]
            == f"Privacy request with ID {privacy_request_id} does not exist, or is not associated with a data rights protocol action."
        )

    @pytest.mark.parametrize(
        "privacy_request_status,expected_drp_status",
        [
            (PrivacyRequestStatus.pending, PrivacyRequestDRPStatus.open),
            (PrivacyRequestStatus.approved, PrivacyRequestDRPStatus.in_progress),
            (PrivacyRequestStatus.denied, PrivacyRequestDRPStatus.denied),
            (PrivacyRequestStatus.in_processing, PrivacyRequestDRPStatus.in_progress),
            (PrivacyRequestStatus.complete, PrivacyRequestDRPStatus.fulfilled),
            (PrivacyRequestStatus.paused, PrivacyRequestDRPStatus.in_progress),
            (PrivacyRequestStatus.error, PrivacyRequestDRPStatus.expired),
        ],
    )
    def test_get_privacy_request_with_drp_action(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header: Callable,
        url_for_privacy_request_with_drp_action: str,
        privacy_request_with_drp_action: PrivacyRequest,
        privacy_request_status: PrivacyRequestStatus,
        expected_drp_status: PrivacyRequestDRPStatus,
    ):
        privacy_request_with_drp_action.status = privacy_request_status
        privacy_request_with_drp_action.save(db=db)
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            url_for_privacy_request_with_drp_action,
            headers=auth_header,
        )
        assert 200 == response.status_code
        assert expected_drp_status.value == response.json()["status"]
        assert privacy_request_with_drp_action.id == response.json()["request_id"]
        assert (
            privacy_request_with_drp_action.requested_at.isoformat()
            == response.json()["received_at"]
        )


class TestGetDrpDataRights:
    """
    Tests for the endpoint to retrieve DRP data rights.
    """

    @pytest.fixture(scope="function")
    def url_for_data_rights(self) -> str:
        return V1_URL_PREFIX + DRP_DATA_RIGHTS

    def test_get_drp_data_rights_no_drp_policy(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header: Callable,
        url_for_data_rights: str,
        policy,
    ):
        expected_response = {
            "version": "0.5",
            "api_base": None,
            "actions": [],
            "user_relationships": None,
        }
        auth_header = generate_auth_header(scopes=[POLICY_READ])
        response = api_client.get(
            url_for_data_rights,
            headers=auth_header,
        )
        assert 200 == response.status_code
        assert response.json() == expected_response

    def test_get_drp_data_rights_one_drp_policy(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header: Callable,
        url_for_data_rights: str,
        policy_drp_action,
    ):
        expected_response = {
            "version": "0.5",
            "api_base": None,
            "actions": [DrpAction.access.value],
            "user_relationships": None,
        }
        auth_header = generate_auth_header(scopes=[POLICY_READ])
        response = api_client.get(
            url_for_data_rights,
            headers=auth_header,
        )
        assert 200 == response.status_code
        assert response.json() == expected_response

    def test_get_drp_data_rights_multiple_drp_policies(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header: Callable,
        url_for_data_rights: str,
        policy_drp_action,
        policy_drp_action_erasure,
    ):
        expected_response = {
            "version": "0.5",
            "api_base": None,
            "actions": [DrpAction.access.value, DrpAction.deletion.value],
            "user_relationships": None,
        }
        auth_header = generate_auth_header(scopes=[POLICY_READ])
        response = api_client.get(
            url_for_data_rights,
            headers=auth_header,
        )
        assert 200 == response.status_code
        assert response.json() == expected_response


class TestDrpRevoke:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + DRP_REVOKE

    def test_revoke_not_authenticated(
        self, api_client: TestClient, privacy_request, url
    ):
        response = api_client.post(url, headers={})
        assert 401 == response.status_code

    def test_revoke_wrong_scope(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(url, headers=auth_header, json={})
        assert 403 == response.status_code

    def test_revoke_wrong_status(
        self, db, api_client: TestClient, generate_auth_header, url, privacy_request
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_REVIEW])
        response = api_client.post(
            url, headers=auth_header, json={"request_id": privacy_request.id}
        )
        assert 400 == response.status_code
        assert response.json()[
            "detail"
        ] == "Invalid revoke request. Can only revoke `pending` requests. Privacy request '{}' status = in_processing.".format(
            privacy_request.id
        )
        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.in_processing
        assert privacy_request.canceled_at is None

    def test_revoke(
        self, db, api_client: TestClient, generate_auth_header, url, privacy_request
    ):
        privacy_request.status = PrivacyRequestStatus.pending
        privacy_request.save(db)
        canceled_reason = "Accidentally submitted"

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_REVIEW])
        response = api_client.post(
            url,
            headers=auth_header,
            json={"request_id": privacy_request.id, "reason": canceled_reason},
        )
        assert 200 == response.status_code
        db.refresh(privacy_request)

        assert privacy_request.status == PrivacyRequestStatus.canceled
        assert privacy_request.cancel_reason == canceled_reason
        assert privacy_request.canceled_at is not None

        data = response.json()
        assert data["request_id"] == privacy_request.id
        assert data["status"] == "revoked"
        assert data["reason"] == canceled_reason
