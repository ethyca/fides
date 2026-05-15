import json
from datetime import datetime, timedelta, timezone
from typing import Generator
from unittest import mock
from uuid import uuid4

import pytest
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from starlette.testclient import TestClient

from fides.api.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
)
from fides.api.models.client import ClientDetail
from fides.api.models.event_audit import EventAudit, EventAuditType
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_email_verification import FidesUserEmailVerification
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.oauth.jwt import generate_jwe
from fides.api.oauth.roles import VIEWER
from fides.api.schemas.messaging.messaging import MessagingActionType
from fides.common.urn_registry import V1_URL_PREFIX
from fides.config import CONFIG

REQUEST_EMAIL_VERIFICATION_URL = V1_URL_PREFIX + "/user/request-email-verification"
VERIFY_EMAIL_WITH_TOKEN_URL = V1_URL_PREFIX + "/user/verify-email-with-token"


def _auth_header_for(user: FidesUser, db) -> dict:
    """Build an Authorization header for the given user, creating a client if needed."""
    if not user.client:
        ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            scopes=[],
            roles=user.permissions.roles if user.permissions else [],
            user_id=user.id,
        )
        db.refresh(user)
    payload = {
        JWE_PAYLOAD_SCOPES: [],
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
    }
    jwe = generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
    return {"Authorization": "Bearer " + jwe}


class TestRequestEmailVerification:
    @pytest.fixture(scope="function")
    def unverified_user(self, db) -> Generator:
        """User with an email but unverified."""
        user = FidesUser.create(
            db=db,
            data={
                "username": "unverified_user",
                "email_address": "unverified@example.com",
                "password": "Testpassword1!",
                "disabled": False,
            },
        )
        FidesUserPermissions.create(
            db=db,
            data={"user_id": user.id, "roles": [VIEWER]},
        )
        yield user
        try:
            user.delete(db)
        except Exception:
            pass

    @pytest.fixture(scope="function")
    def verified_user(self, db) -> Generator:
        """User with a verified email."""
        user = FidesUser.create(
            db=db,
            data={
                "username": "already_verified",
                "email_address": "verified@example.com",
                "password": "Testpassword1!",
                "disabled": False,
            },
        )
        user.email_verified_at = datetime.now(timezone.utc)
        user.save(db)
        FidesUserPermissions.create(
            db=db,
            data={"user_id": user.id, "roles": [VIEWER]},
        )
        yield user
        try:
            user.delete(db)
        except Exception:
            pass

    @pytest.fixture(scope="function")
    def emailless_user(self, db) -> Generator:
        """User with no email address."""
        user = FidesUser.create(
            db=db,
            data={
                "username": "no_email_user",
                "password": "Testpassword1!",
                "disabled": False,
            },
        )
        FidesUserPermissions.create(
            db=db,
            data={"user_id": user.id, "roles": [VIEWER]},
        )
        yield user
        try:
            user.delete(db)
        except Exception:
            pass

    def test_request_email_verification_unauthenticated_rejected(
        self, api_client: TestClient
    ):
        """Endpoint requires authentication."""
        response = api_client.post(REQUEST_EMAIL_VERIFICATION_URL)
        assert response.status_code in (HTTP_401_UNAUTHORIZED, 403)

    def test_request_email_verification_dispatches_for_unverified(
        self, db, api_client: TestClient, unverified_user
    ):
        """Authenticated unverified user with messaging enabled gets an email."""
        headers = _auth_header_for(unverified_user, db)
        with (
            mock.patch(
                "fides.service.messaging.messaging_service.MessagingService.is_email_invite_enabled",
                return_value=True,
            ),
            mock.patch(
                "fides.service.user.user_service.dispatch_message"
            ) as mock_dispatch,
        ):
            response = api_client.post(REQUEST_EMAIL_VERIFICATION_URL, headers=headers)
        assert response.status_code == HTTP_200_OK
        assert "verification email" in response.json()["detail"]
        mock_dispatch.assert_called_once()
        call_kwargs = mock_dispatch.call_args
        assert call_kwargs[1]["action_type"] == MessagingActionType.EMAIL_VERIFICATION

    def test_request_email_verification_skipped_for_already_verified(
        self, db, api_client: TestClient, verified_user
    ):
        """Already-verified user gets a 200 but no email dispatched."""
        headers = _auth_header_for(verified_user, db)
        with (
            mock.patch(
                "fides.service.messaging.messaging_service.MessagingService.is_email_invite_enabled",
                return_value=True,
            ),
            mock.patch(
                "fides.service.user.user_service.dispatch_message"
            ) as mock_dispatch,
        ):
            response = api_client.post(REQUEST_EMAIL_VERIFICATION_URL, headers=headers)
        assert response.status_code == HTTP_200_OK
        mock_dispatch.assert_not_called()

    def test_request_email_verification_skipped_for_no_email(
        self, db, api_client: TestClient, emailless_user
    ):
        """User without an email gets a 200 but no email dispatched."""
        headers = _auth_header_for(emailless_user, db)
        with (
            mock.patch(
                "fides.service.messaging.messaging_service.MessagingService.is_email_invite_enabled",
                return_value=True,
            ),
            mock.patch(
                "fides.service.user.user_service.dispatch_message"
            ) as mock_dispatch,
        ):
            response = api_client.post(REQUEST_EMAIL_VERIFICATION_URL, headers=headers)
        assert response.status_code == HTTP_200_OK
        mock_dispatch.assert_not_called()

    def test_request_email_verification_skipped_when_messaging_unconfigured(
        self, db, api_client: TestClient, unverified_user
    ):
        """Messaging disabled → no email dispatched."""
        headers = _auth_header_for(unverified_user, db)
        with (
            mock.patch(
                "fides.service.messaging.messaging_service.MessagingService.is_email_invite_enabled",
                return_value=False,
            ),
            mock.patch(
                "fides.service.user.user_service.dispatch_message"
            ) as mock_dispatch,
        ):
            response = api_client.post(REQUEST_EMAIL_VERIFICATION_URL, headers=headers)
        assert response.status_code == HTTP_200_OK
        mock_dispatch.assert_not_called()

    def test_request_email_verification_creates_token(
        self, db, api_client: TestClient, unverified_user
    ):
        """A verification token record is created in the DB."""
        headers = _auth_header_for(unverified_user, db)
        with (
            mock.patch(
                "fides.service.messaging.messaging_service.MessagingService.is_email_invite_enabled",
                return_value=True,
            ),
            mock.patch("fides.service.user.user_service.dispatch_message"),
        ):
            api_client.post(REQUEST_EMAIL_VERIFICATION_URL, headers=headers)

        record = FidesUserEmailVerification.get_by(
            db, field="user_id", value=unverified_user.id
        )
        assert record is not None
        record.delete(db)

    def test_request_email_verification_skipped_for_disabled_user(
        self, db, api_client: TestClient, unverified_user
    ):
        """Disabled user gets a 200 but no email dispatched."""
        unverified_user.disabled = True
        unverified_user.save(db)
        headers = _auth_header_for(unverified_user, db)
        with (
            mock.patch(
                "fides.service.messaging.messaging_service.MessagingService.is_email_invite_enabled",
                return_value=True,
            ),
            mock.patch(
                "fides.service.user.user_service.dispatch_message"
            ) as mock_dispatch,
        ):
            response = api_client.post(REQUEST_EMAIL_VERIFICATION_URL, headers=headers)
        assert response.status_code == HTTP_200_OK
        mock_dispatch.assert_not_called()

    def test_request_email_verification_audits_failure_on_dispatch_exception(
        self, db, api_client: TestClient, unverified_user
    ):
        """A dispatch exception is swallowed; endpoint still returns 200 and a
        failed audit event is written."""
        headers = _auth_header_for(unverified_user, db)
        with (
            mock.patch(
                "fides.service.messaging.messaging_service.MessagingService.is_email_invite_enabled",
                return_value=True,
            ),
            mock.patch(
                "fides.service.user.user_service.dispatch_message",
                side_effect=Exception("boom"),
            ),
        ):
            response = api_client.post(REQUEST_EMAIL_VERIFICATION_URL, headers=headers)
        assert response.status_code == HTTP_200_OK

        failed = (
            db.query(EventAudit)
            .filter_by(
                event_type=EventAuditType.email_verification_requested.value,
                user_id=unverified_user.id,
                status="failed",
            )
            .first()
        )
        assert failed is not None

    def test_request_email_verification_replaces_existing_token(
        self, db, api_client: TestClient, unverified_user
    ):
        """Requesting a new verification replaces the old token."""
        token1 = str(uuid4())
        FidesUserEmailVerification.create_or_replace(
            db, user_id=unverified_user.id, token=token1
        )

        headers = _auth_header_for(unverified_user, db)
        with (
            mock.patch(
                "fides.service.messaging.messaging_service.MessagingService.is_email_invite_enabled",
                return_value=True,
            ),
            mock.patch("fides.service.user.user_service.dispatch_message"),
        ):
            api_client.post(REQUEST_EMAIL_VERIFICATION_URL, headers=headers)

        records = (
            db.query(FidesUserEmailVerification)
            .filter_by(user_id=unverified_user.id)
            .all()
        )
        assert len(records) == 1
        assert not records[0].token_valid(token1)
        records[0].delete(db)


class TestVerifyEmailWithToken:
    @pytest.fixture(scope="function")
    def user_with_verification_token(self, db) -> Generator:
        """Create an unverified user with a valid verification token."""
        user = FidesUser.create(
            db=db,
            data={
                "username": "verify_target",
                "email_address": "verify_target@example.com",
                "password": "Testpassword1!",
                "disabled": False,
            },
        )
        FidesUserPermissions.create(
            db=db,
            data={"user_id": user.id, "roles": [VIEWER]},
        )

        token = str(uuid4())
        FidesUserEmailVerification.create_or_replace(db, user_id=user.id, token=token)

        yield user, token
        try:
            user.delete(db)
        except Exception:
            pass

    def test_verify_email_with_valid_token(
        self, db, api_client: TestClient, user_with_verification_token
    ):
        """A valid token verifies the email and returns a login response."""
        user, token = user_with_verification_token
        assert user.email_verified_at is None

        response = api_client.post(
            VERIFY_EMAIL_WITH_TOKEN_URL,
            json={"username": "verify_target", "token": token},
        )
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert "user_data" in data
        assert "token_data" in data
        assert data["user_data"]["username"] == "verify_target"
        assert data["user_data"]["email_verified_at"] is not None

        db.refresh(user)
        assert user.email_verified_at is not None

        # Single-use: token deleted
        record = FidesUserEmailVerification.get_by(db, field="user_id", value=user.id)
        assert record is None

        # Completion audit event recorded
        completed = (
            db.query(EventAudit)
            .filter_by(
                event_type=EventAuditType.email_verification_completed.value,
                user_id=user.id,
            )
            .first()
        )
        assert completed is not None

    def test_verify_email_with_invalid_token(self, api_client: TestClient):
        """Unknown username/token returns a generic 400."""
        response = api_client.post(
            VERIFY_EMAIL_WITH_TOKEN_URL,
            json={"username": "nonexistent_user", "token": "invalid-token"},
        )
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert "Invalid or expired" in response.json()["detail"]

    def test_verify_email_with_no_verification_record(self, db, api_client: TestClient):
        """User exists but has no verification record → generic 400 (no enumeration)."""
        user = FidesUser.create(
            db=db,
            data={
                "username": "no_record_user",
                "email_address": "no_record@example.com",
                "password": "Testpassword1!",
                "disabled": False,
            },
        )
        FidesUserPermissions.create(
            db=db,
            data={"user_id": user.id, "roles": [VIEWER]},
        )
        try:
            response = api_client.post(
                VERIFY_EMAIL_WITH_TOKEN_URL,
                json={"username": "no_record_user", "token": "anything"},
            )
            assert response.status_code == HTTP_400_BAD_REQUEST
            assert "Invalid or expired" in response.json()["detail"]
        finally:
            user.delete(db)

    def test_verify_email_with_wrong_plaintext_token(
        self, db, api_client: TestClient, user_with_verification_token
    ):
        """User and verification record exist, but the plaintext token doesn't
        match the stored hash → generic 400."""
        _user, _real_token = user_with_verification_token
        response = api_client.post(
            VERIFY_EMAIL_WITH_TOKEN_URL,
            json={"username": "verify_target", "token": "completely-wrong-token"},
        )
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert "Invalid or expired" in response.json()["detail"]

    def test_verify_email_with_expired_token(
        self, db, api_client: TestClient, user_with_verification_token
    ):
        """An expired token returns a generic 400 and writes an audit event."""
        user, token = user_with_verification_token

        record = FidesUserEmailVerification.get_by(db, field="user_id", value=user.id)
        record.created_at = datetime.now(timezone.utc) - timedelta(hours=24)
        record.save(db)

        response = api_client.post(
            VERIFY_EMAIL_WITH_TOKEN_URL,
            json={"username": "verify_target", "token": token},
        )
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert "Invalid or expired" in response.json()["detail"]

        expired_event = (
            db.query(EventAudit)
            .filter_by(
                event_type=EventAuditType.email_verification_token_expired.value,
                user_id=user.id,
            )
            .first()
        )
        assert expired_event is not None

        # Expired token row deleted
        record_after = FidesUserEmailVerification.get_by(
            db, field="user_id", value=user.id
        )
        assert record_after is None
