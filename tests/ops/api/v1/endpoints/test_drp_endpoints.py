from datetime import datetime
from unittest import mock
from uuid import uuid4

import jwt
import pytest

from fides.api.ops.api.v1.scope_registry import (
    POLICY_READ,
    PRIVACY_REQUEST_READ,
    PRIVACY_REQUEST_REVIEW,
    STORAGE_CREATE_OR_UPDATE,
)
from fides.api.ops.api.v1.urn_registry import (
    DRP_DATA_RIGHTS,
    DRP_EXERCISE,
    DRP_REVOKE,
    DRP_STATUS,
    V1_URL_PREFIX,
)
from fides.api.ops.models.policy import DrpAction
from fides.api.ops.models.privacy_request import (
    PrivacyRequest,
    PrivacyRequestError,
    PrivacyRequestNotifications,
    PrivacyRequestStatus,
)
from fides.api.ops.schemas.privacy_request import PrivacyRequestDRPStatus
from fides.api.ops.util.cache import (
    get_drp_request_body_cache_key,
    get_identity_cache_key,
)


class TestCreateDrpPrivacyRequest:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + DRP_EXERCISE

    @mock.patch(
        "fides.api.ops.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_drp_privacy_request(
        self,
        run_access_request_mock,
        url,
        db,
        api_client,
        cache,
        config,
    ):
        TEST_EMAIL = "test@example.com"
        TEST_PHONE_NUMBER = "+12345678910"
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
        assert cache.get(identity_key) == encoded_identity
        fidesops_identity_key = get_identity_cache_key(
            privacy_request_id=pr.id,
            identity_attribute="email",
        )
        assert cache.get(fidesops_identity_key) == identity["email"]
        persisted_identity = pr.get_persisted_identity()
        assert persisted_identity.email == TEST_EMAIL
        assert persisted_identity.phone_number == TEST_PHONE_NUMBER
        assert run_access_request_mock.called

    @pytest.mark.usefixtures("policy_drp_action")
    @mock.patch(
        "fides.api.ops.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_drp_privacy_request_unsupported_identity_props(
        self,
        run_access_request_mock,
        url,
        db,
        api_client,
        cache,
        config,
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
        assert cache.get(identity_key) == encoded_identity
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
        assert run_access_request_mock.called

    @pytest.mark.usefixtures("policy_drp_action")
    def test_create_drp_privacy_request_no_jwt(
        self,
        url,
        api_client,
        config,
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

    @pytest.mark.usefixtures("policy_drp_action")
    def test_create_drp_privacy_request_no_exercise(
        self,
        url,
        api_client,
        config,
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

    @pytest.mark.usefixtures("policy_drp_action")
    def test_create_drp_privacy_request_invalid_exercise(
        self,
        url,
        api_client,
        config,
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

    @pytest.mark.usefixtures("policy")
    def test_create_drp_privacy_request_no_associated_policy(
        self,
        url,
        api_client,
        config,
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

    @pytest.mark.usefixtures("messaging_config", "policy_drp_action")
    @mock.patch(
        "fides.api.ops.service.messaging.message_dispatch_service._mailgun_dispatcher"
    )
    @mock.patch(
        "fides.api.ops.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_drp_privacy_request_error_notification(
        self,
        mailgun_dispatcher_mock,
        run_access_request_mock,
        url,
        db,
        api_client,
        cache,
        policy,
        config,
    ):
        TEST_EMAIL = "test@example.com"
        TEST_PHONE_NUMBER = "+12345678910"
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

        PrivacyRequestNotifications.create(
            db=db,
            data={
                "email": "some@email.com, another@email.com",
                "notify_after_failures": 1,
            },
        )

        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "external_id": f"ext-{str(uuid4())}",
                "started_processing_at": datetime(2021, 1, 1),
                "finished_processing_at": datetime(2021, 1, 1),
                "requested_at": datetime(2021, 1, 1),
                "status": PrivacyRequestStatus.error,
                "origin": "https://example.com/",
                "policy_id": policy.id,
                "client_id": policy.client_id,
            },
        )

        privacy_request.error_processing(db)

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
        assert cache.get(identity_key) == encoded_identity
        fidesops_identity_key = get_identity_cache_key(
            privacy_request_id=pr.id,
            identity_attribute="email",
        )
        assert cache.get(fidesops_identity_key) == identity["email"]
        persisted_identity = pr.get_persisted_identity()
        assert persisted_identity.email == TEST_EMAIL
        assert persisted_identity.phone_number == TEST_PHONE_NUMBER

        sent_errors = PrivacyRequestError.filter(
            db=db, conditions=(PrivacyRequestError.message_sent.is_(True))
        ).all()

        assert len(sent_errors) == 1

        assert run_access_request_mock.called
        assert mailgun_dispatcher_mock.called


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
        api_client,
        url_for_privacy_request,
    ):
        response = api_client.get(
            url_for_privacy_request,
            headers={},
        )
        assert 401 == response.status_code

    @pytest.mark.parametrize("auth_header", [[STORAGE_CREATE_OR_UPDATE]], indirect=True)
    def test_get_privacy_requests_wrong_scope(
        self,
        auth_header,
        api_client,
        url_for_privacy_request,
    ):
        response = api_client.get(
            url_for_privacy_request,
            headers=auth_header,
        )
        assert 403 == response.status_code

    @pytest.mark.parametrize("auth_header", [[PRIVACY_REQUEST_READ]], indirect=True)
    def test_get_non_drp_privacy_request(
        self,
        auth_header,
        api_client,
        url_for_privacy_request,
    ):
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
    @pytest.mark.parametrize("auth_header", [[PRIVACY_REQUEST_READ]], indirect=True)
    def test_get_privacy_request_with_drp_action(
        self,
        auth_header,
        api_client,
        db,
        url_for_privacy_request_with_drp_action,
        privacy_request_with_drp_action,
        privacy_request_status,
        expected_drp_status,
    ):
        privacy_request_with_drp_action.status = privacy_request_status
        privacy_request_with_drp_action.save(db=db)
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

    @pytest.mark.usefixtures("policy")
    @pytest.mark.parametrize("auth_header", [[POLICY_READ]], indirect=True)
    def test_get_drp_data_rights_no_drp_policy(
        self,
        auth_header,
        api_client,
        url_for_data_rights,
    ):
        expected_response = {
            "version": "0.5",
            "api_base": None,
            "actions": [],
            "user_relationships": None,
        }
        response = api_client.get(
            url_for_data_rights,
            headers=auth_header,
        )
        assert 200 == response.status_code
        assert response.json() == expected_response

    @pytest.mark.usefixtures("policy_drp_action")
    @pytest.mark.parametrize("auth_header", [[POLICY_READ]], indirect=True)
    def test_get_drp_data_rights_one_drp_policy(
        self,
        auth_header,
        api_client,
        url_for_data_rights,
    ):
        expected_response = {
            "version": "0.5",
            "api_base": None,
            "actions": [DrpAction.access.value],
            "user_relationships": None,
        }
        response = api_client.get(
            url_for_data_rights,
            headers=auth_header,
        )
        assert 200 == response.status_code
        assert response.json() == expected_response

    @pytest.mark.usefixtures("policy_drp_action", "policy_drp_action_erasure")
    @pytest.mark.parametrize("auth_header", [[POLICY_READ]], indirect=True)
    def test_get_drp_data_rights_multiple_drp_policies(
        self,
        auth_header,
        api_client,
        url_for_data_rights,
    ):
        expected_response = {
            "version": "0.5",
            "api_base": None,
            "actions": [DrpAction.access.value, DrpAction.deletion.value],
            "user_relationships": None,
        }
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

    @pytest.mark.usefixtures("privacy_request")
    def test_revoke_not_authenticated(self, api_client, url):
        response = api_client.post(url, headers={})
        assert 401 == response.status_code

    @pytest.mark.parametrize("auth_header", [[PRIVACY_REQUEST_READ]], indirect=True)
    def test_revoke_wrong_scope(self, auth_header, api_client, url):
        response = api_client.post(url, headers=auth_header, json={})
        assert 403 == response.status_code

    @pytest.mark.parametrize("auth_header", [[PRIVACY_REQUEST_REVIEW]], indirect=True)
    def test_revoke_wrong_status(
        self, auth_header, db, api_client, url, privacy_request
    ):
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

    @pytest.mark.parametrize("auth_header", [[PRIVACY_REQUEST_REVIEW]], indirect=True)
    def test_revoke(self, auth_header, db, api_client, url, privacy_request):
        privacy_request.status = PrivacyRequestStatus.pending
        privacy_request.save(db)
        canceled_reason = "Accidentally submitted"

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
