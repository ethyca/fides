from datetime import datetime, timedelta, timezone
from typing import Generator
from unittest import mock
from uuid import uuid4

import pytest
from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
)
from starlette.testclient import TestClient

from fides.api.cryptography.cryptographic_util import str_to_b64_str
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_invite import FidesUserInvite
from fides.api.models.fides_user_password_reset import FidesUserPasswordReset
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.oauth.roles import VIEWER
from fides.api.schemas.messaging.messaging import MessagingActionType
from fides.common.urn_registry import V1_URL_PREFIX
from fides.config import CONFIG

FORGOT_PASSWORD_URL = V1_URL_PREFIX + "/user/forgot-password"
RESET_PASSWORD_WITH_TOKEN_URL = V1_URL_PREFIX + "/user/reset-password-with-token"
ACCEPT_INVITE_URL = V1_URL_PREFIX + "/user/accept-invite"


class TestForgotPassword:
    @pytest.fixture(scope="function")
    def verified_user(self, db) -> Generator:
        """Create a user with a verified email."""
        user = FidesUser.create(
            db=db,
            data={
                "username": "verified_user",
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
        user.delete(db)

    @pytest.fixture(scope="function")
    def unverified_user(self, db) -> Generator:
        """Create a user without a verified email."""
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
        user.delete(db)

    def test_forgot_password_returns_200_for_verified_user(
        self, api_client: TestClient, verified_user
    ):
        """Test that forgot-password returns 200 and dispatches email for a verified user."""
        with (
            mock.patch(
                "fides.service.messaging.messaging_service.MessagingService.is_email_invite_enabled",
                return_value=True,
            ),
            mock.patch(
                "fides.service.user.user_service.dispatch_message"
            ) as mock_dispatch,
        ):
            response = api_client.post(
                FORGOT_PASSWORD_URL,
                json={"email": "verified@example.com"},
            )
        assert response.status_code == HTTP_200_OK
        assert "password reset link" in response.json()["detail"]
        mock_dispatch.assert_called_once()
        call_kwargs = mock_dispatch.call_args
        assert call_kwargs[1]["action_type"] == MessagingActionType.PASSWORD_RESET

    def test_forgot_password_returns_200_for_unknown_email(
        self, api_client: TestClient
    ):
        """Test that forgot-password returns 200 even for unknown emails (OWASP)."""
        response = api_client.post(
            FORGOT_PASSWORD_URL,
            json={"email": "nonexistent@example.com"},
        )
        assert response.status_code == HTTP_200_OK

    def test_forgot_password_returns_200_for_unverified_email(
        self, api_client: TestClient, unverified_user
    ):
        """Test that forgot-password returns 200 but does NOT send email for unverified user."""
        with mock.patch(
            "fides.service.user.user_service.dispatch_message"
        ) as mock_dispatch:
            response = api_client.post(
                FORGOT_PASSWORD_URL,
                json={"email": "unverified@example.com"},
            )
        assert response.status_code == HTTP_200_OK
        mock_dispatch.assert_not_called()

    def test_forgot_password_creates_reset_token(
        self, db, api_client: TestClient, verified_user
    ):
        """Test that a reset token is created in the database."""
        with (
            mock.patch(
                "fides.service.messaging.messaging_service.MessagingService.is_email_invite_enabled",
                return_value=True,
            ),
            mock.patch("fides.service.user.user_service.dispatch_message"),
        ):
            api_client.post(
                FORGOT_PASSWORD_URL,
                json={"email": "verified@example.com"},
            )

        reset = FidesUserPasswordReset.get_by(
            db, field="user_id", value=verified_user.id
        )
        assert reset is not None
        reset.delete(db)

    def test_forgot_password_replaces_existing_token(
        self, db, api_client: TestClient, verified_user
    ):
        """Test that requesting a new reset replaces the old token."""
        token1 = str(uuid4())
        FidesUserPasswordReset.create_or_replace(
            db, user_id=verified_user.id, token=token1
        )

        with (
            mock.patch(
                "fides.service.messaging.messaging_service.MessagingService.is_email_invite_enabled",
                return_value=True,
            ),
            mock.patch("fides.service.user.user_service.dispatch_message"),
        ):
            api_client.post(
                FORGOT_PASSWORD_URL,
                json={"email": "verified@example.com"},
            )

        resets = (
            db.query(FidesUserPasswordReset).filter_by(user_id=verified_user.id).all()
        )
        assert len(resets) == 1
        # The old token should no longer be valid
        assert not resets[0].token_valid(token1)
        resets[0].delete(db)


class TestResetPasswordWithToken:
    @pytest.fixture(scope="function")
    def user_with_reset_token(self, db) -> Generator:
        """Create a user with a verified email and a reset token."""
        user = FidesUser.create(
            db=db,
            data={
                "username": "reset_user",
                "email_address": "reset@example.com",
                "password": "OldPassword1!",
                "disabled": False,
            },
        )
        user.email_verified_at = datetime.now(timezone.utc)
        user.save(db)
        FidesUserPermissions.create(
            db=db,
            data={"user_id": user.id, "roles": [VIEWER]},
        )

        token = str(uuid4())
        FidesUserPasswordReset.create_or_replace(db, user_id=user.id, token=token)

        yield user, token
        try:
            user.delete(db)
        except Exception:
            pass

    def test_reset_password_with_valid_token(
        self, db, api_client: TestClient, user_with_reset_token
    ):
        """Test successful password reset with a valid token."""
        user, token = user_with_reset_token
        new_password = "NewPassword1!"

        response = api_client.post(
            RESET_PASSWORD_WITH_TOKEN_URL,
            json={
                "username": "reset_user",
                "token": token,
                "new_password": str_to_b64_str(new_password),
            },
        )
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert "user_data" in data
        assert "token_data" in data
        assert data["user_data"]["username"] == "reset_user"

        # Verify new password works
        db.refresh(user)
        assert user.credentials_valid(new_password)

        # Verify reset token is deleted (single-use)
        reset = FidesUserPasswordReset.get_by(db, field="user_id", value=user.id)
        assert reset is None

    def test_reset_password_with_invalid_token(self, api_client: TestClient):
        """Test that an invalid token returns 400."""
        response = api_client.post(
            RESET_PASSWORD_WITH_TOKEN_URL,
            json={
                "username": "nonexistent_user",
                "token": "invalid-token",
                "new_password": str_to_b64_str("NewPassword1!"),
            },
        )
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert "Invalid or expired" in response.json()["detail"]

    def test_reset_password_with_expired_token(
        self, db, api_client: TestClient, user_with_reset_token
    ):
        """Test that an expired token returns 400."""
        user, token = user_with_reset_token

        # Manually expire the token by setting created_at to the past
        reset = FidesUserPasswordReset.get_by(db, field="user_id", value=user.id)
        reset.created_at = datetime.now(timezone.utc) - timedelta(hours=24)
        reset.save(db)

        response = api_client.post(
            RESET_PASSWORD_WITH_TOKEN_URL,
            json={
                "username": "reset_user",
                "token": token,
                "new_password": str_to_b64_str("NewPassword1!"),
            },
        )
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert "Invalid or expired" in response.json()["detail"]

    def test_reset_password_invalidates_existing_sessions(
        self, db, api_client: TestClient, user_with_reset_token
    ):
        """Test that resetting password deletes the old OAuth client (invalidates sessions)."""
        user, token = user_with_reset_token

        response = api_client.post(
            RESET_PASSWORD_WITH_TOKEN_URL,
            json={
                "username": "reset_user",
                "token": token,
                "new_password": str_to_b64_str("NewPassword1!"),
            },
        )
        assert response.status_code == HTTP_200_OK

    def test_reset_password_weak_password_rejected(
        self, api_client: TestClient, user_with_reset_token
    ):
        """Test that a weak password is rejected."""
        _, token = user_with_reset_token
        response = api_client.post(
            RESET_PASSWORD_WITH_TOKEN_URL,
            json={
                "username": "reset_user",
                "token": token,
                "new_password": str_to_b64_str("weak"),
            },
        )
        assert response.status_code == 422


class TestAcceptInviteSetsEmailVerified:
    @pytest.fixture(scope="function")
    def invited_user_for_verification(self, db) -> Generator:
        """Create a user with a pending invitation to verify email_verified_at gets set."""
        user = FidesUser.create(
            db=db,
            data={
                "username": "verify_email_user",
                "email_address": "verify_email@example.com",
                "disabled": True,
                "disabled_reason": "pending_invite",
            },
        )
        FidesUserPermissions.create(
            db=db,
            data={"user_id": user.id, "roles": [VIEWER]},
        )
        invite_code = str(uuid4())
        FidesUserInvite.create(
            db=db,
            data={"username": "verify_email_user", "invite_code": invite_code},
        )
        yield user, invite_code
        try:
            user.delete(db)
        except Exception:
            pass

    def test_accept_invite_sets_email_verified_at(
        self, db, api_client: TestClient, invited_user_for_verification
    ):
        """Test that accepting an invite sets email_verified_at on the user."""
        user, invite_code = invited_user_for_verification

        assert user.email_verified_at is None

        response = api_client.post(
            ACCEPT_INVITE_URL,
            params={"username": "verify_email_user", "invite_code": invite_code},
            json={"new_password": str_to_b64_str("NewPassword1!")},
        )
        assert response.status_code == HTTP_200_OK

        db.refresh(user)
        assert user.email_verified_at is not None
        assert user.disabled is False
