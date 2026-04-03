import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import AuthorizationError
from fides.api.db.encryption_utils import get_encryption_key
from fides.api.models.client import ClientDetail
from fides.api.models.event_audit import EventAudit, EventAuditStatus, EventAuditType
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_invite import FidesUserInvite
from fides.api.models.fides_user_password_reset import FidesUserPasswordReset
from fides.api.schemas.messaging.messaging import (
    MessagingActionType,
    PasswordResetBodyParams,
    UserInviteBodyParams,
)
from fides.api.schemas.redis_cache import Identity
from fides.api.service.messaging.message_dispatch_service import dispatch_message
from fides.api.util.errors import FidesError, MessageDispatchException
from fides.config import FidesConfig
from fides.config.config_proxy import ConfigProxy
from fides.service.messaging.messaging_service import MessagingService


class UserService:
    def __init__(
        self,
        db: Session,
        config: FidesConfig,
        config_proxy: ConfigProxy,
        messaging_service: MessagingService,
    ):
        self.db = db
        self.config = config
        self.config_proxy = config_proxy
        self.messaging_service = messaging_service

    def invite_user(self, user: FidesUser) -> None:
        """
        Generates a user invite and sends the invite code to the user via email.

        This is a no-op if email messaging isn't configured.
        """

        if self.messaging_service.is_email_invite_enabled():
            invite_code = str(uuid.uuid4())
            FidesUserInvite.create(
                db=self.db, data={"username": user.username, "invite_code": invite_code}
            )
            user.update(
                self.db, data={"disabled": True, "disabled_reason": "pending_invite"}
            )
            # TODO: refactor to use MessagingService
            dispatch_message(
                self.db,
                action_type=MessagingActionType.USER_INVITE,
                to_identity=Identity(email=user.email_address),
                service_type=self.config_proxy.notifications.notification_service_type,
                message_body_params=UserInviteBodyParams(
                    username=user.username, invite_code=invite_code
                ),
            )
        else:
            logger.debug(
                "Skipping invitation email, an email messaging provider is not enabled",
            )

    def perform_login(
        self,
        client_id_byte_length: int,
        client_secret_byte_length: int,
        user: FidesUser,
        skip_save: Optional[bool] = False,
    ) -> ClientDetail:
        """Performs a login by updating the FidesUser instance and creating and returning
        an associated ClientDetail.

        If the username or password was bad, skip_save should be True. We still run through
        parallel operations to keep the timing of operations similar, but should skip
        saving to the database.
        """

        client = user.client
        if not client:
            logger.info("Creating client for login")
            client, _ = ClientDetail.create_client_and_secret(
                self.db,
                client_id_byte_length,
                client_secret_byte_length,
                scopes=[],  # type: ignore
                roles=user.permissions.roles,  # type: ignore
                systems=user.system_ids,  # type: ignore
                monitors=user.stewarded_monitor_ids,  # type: ignore
                user_id=user.id,
                in_memory=skip_save,  # If login flow has already errored, don't persist this to the database
            )
        else:
            # Refresh the client just in case - for example, scopes and roles were added via the db directly.
            client.roles = user.permissions.roles  # type: ignore
            client.systems = user.system_ids  # type: ignore
            client.monitors = user.stewarded_monitor_ids  # type: ignore
            if not skip_save:
                client.save(self.db)

        if user.permissions and (not user.permissions.roles and not user.systems):  # type: ignore
            logger.warning("User {} needs roles or systems to login.", user.id)
            raise AuthorizationError(detail="Not Authorized for this action")

        if not skip_save:
            user.last_login_at = datetime.utcnow()
            user.save(self.db)

        return client

    def accept_invite(
        self, user: FidesUser, new_password: str
    ) -> Tuple[FidesUser, str]:
        """
        Updates the user password and enables the user. Also removes the user invite from the database.
        Returns a tuple of the updated user and their access code.
        """

        # update password, enable, and mark email as verified
        # (the user proved email ownership by clicking the invite link)
        user.update_password(db=self.db, new_password=new_password)
        user.update(
            self.db,
            data={
                "disabled": False,
                "disabled_reason": None,
                "email_verified_at": datetime.now(timezone.utc),
            },
        )
        self.db.refresh(user)

        # delete invite
        if user.username:
            invite = FidesUserInvite.get_by(
                db=self.db, field="username", value=user.username
            )
            if invite:
                invite.delete(self.db)
        else:
            logger.warning("Username is missing, skipping invite deletion.")

        client = self.perform_login(
            self.config.security.oauth_client_id_length_bytes,
            self.config.security.oauth_client_secret_length_bytes,
            user,
        )

        logger.info("Creating login access token")
        access_code = client.create_access_code_jwe(
            get_encryption_key(),
            token_expire_minutes=self.config.security.oauth_access_token_expire_minutes,
        )

        return user, access_code

    def reinvite_user(self, user: FidesUser) -> None:
        """
        Reinvites a user who has a pending invitation by generating a new invite code
        and sending a new invitation email.

        Raises:
            FidesError: If the user has no pending invitation or the email fails to send.
        """
        user_invite = FidesUserInvite.get_by(
            self.db, field="username", value=user.username
        )

        if not user_invite:
            raise FidesError("User does not have a pending invitation.")

        new_invite_code = str(uuid.uuid4())
        user_invite.renew_invite(self.db, new_invite_code)

        try:
            dispatch_message(
                self.db,
                action_type=MessagingActionType.USER_INVITE,
                to_identity=Identity(email=user.email_address),
                service_type=self.config_proxy.notifications.notification_service_type,
                message_body_params=UserInviteBodyParams(
                    username=user.username, invite_code=new_invite_code
                ),
            )
        except Exception as exc:
            logger.exception("Failed to dispatch reinvite email")
            raise MessageDispatchException(
                "Failed to send invitation email. Please try again."
            ) from exc

        logger.info("Reinvite email dispatched for pending user")

    def request_password_reset(self, email: str) -> None:
        """
        Initiates a self-service password reset flow for the given email address.

        Always succeeds silently to avoid leaking whether the email exists (OWASP).
        Only sends a reset email if the user exists and has a verified email address.
        """
        user = FidesUser.get_by(self.db, field="email_address", value=email)

        if not user:
            logger.debug("Password reset requested for unknown email")
            return

        if not user.email_verified_at:
            logger.debug("Password reset requested for user without verified email")
            return

        if user.disabled:
            logger.debug("Password reset requested for disabled user")
            return

        if not self.messaging_service.is_email_invite_enabled():
            logger.debug(
                "Password reset requested but email messaging is not configured"
            )
            return

        reset_token = str(uuid.uuid4())
        FidesUserPasswordReset.create_or_replace(
            self.db, user_id=user.id, token=reset_token
        )

        ttl_minutes = self.config.security.password_reset_token_ttl_minutes

        try:
            dispatch_message(
                self.db,
                action_type=MessagingActionType.PASSWORD_RESET,
                to_identity=Identity(email=user.email_address),
                service_type=self.config_proxy.notifications.notification_service_type,
                message_body_params=PasswordResetBodyParams(
                    username=user.username,
                    reset_token=reset_token,
                    ttl_minutes=ttl_minutes,
                ),
            )
        except Exception:
            logger.exception("Failed to dispatch password reset email")
            # Don't raise — always return success to avoid user enumeration

        EventAudit.create(
            self.db,
            data={
                "event_type": EventAuditType.password_reset_requested,
                "user_id": user.id,
                "resource_type": "user",
                "resource_identifier": user.id,
                "description": "Password reset requested",
                "status": EventAuditStatus.succeeded,
            },
        )
        logger.info("Password reset flow initiated")

    def reset_password_with_token(
        self, token: str, new_password: str
    ) -> Tuple[FidesUser, str]:
        """
        Validates a password reset token and resets the user's password.

        Returns a tuple of (user, access_code) on success.

        Raises:
            FidesError: If the token is invalid, expired, or the user is not found.
        """
        # Look through all reset records to find a matching token.
        # There should only be one per user, and tokens are short-lived.
        all_resets = self.db.query(FidesUserPasswordReset).all()
        matching_reset = None
        for reset in all_resets:
            if reset.token_valid(token):
                matching_reset = reset
                break

        if not matching_reset:
            raise FidesError("Invalid or expired password reset token.")

        if matching_reset.is_expired():
            EventAudit.create(
                self.db,
                data={
                    "event_type": EventAuditType.password_reset_token_expired,
                    "user_id": matching_reset.user_id,
                    "resource_type": "user",
                    "resource_identifier": matching_reset.user_id,
                    "description": "Password reset token expired",
                    "status": EventAuditStatus.failed,
                },
            )
            matching_reset.delete(self.db)
            raise FidesError("Invalid or expired password reset token.")

        user = FidesUser.get(self.db, object_id=matching_reset.user_id)
        if not user:
            matching_reset.delete(self.db)
            raise FidesError("Invalid or expired password reset token.")

        # Reset password
        user.update_password(db=self.db, new_password=new_password)

        # Invalidate all existing sessions
        if user.client:
            try:
                user.client.delete(self.db)
            except Exception:
                logger.exception("Unable to delete user client during password reset")

        # Delete the reset token (single-use)
        matching_reset.delete(self.db)

        EventAudit.create(
            self.db,
            data={
                "event_type": EventAuditType.password_reset_completed,
                "user_id": user.id,
                "resource_type": "user",
                "resource_identifier": user.id,
                "description": "Password changed via self-service reset",
                "status": EventAuditStatus.succeeded,
            },
        )

        # Perform login
        client = self.perform_login(
            self.config.security.oauth_client_id_length_bytes,
            self.config.security.oauth_client_secret_length_bytes,
            user,
        )

        logger.info("Creating login access token")
        access_code = client.create_access_code_jwe(
            get_encryption_key(),
            token_expire_minutes=self.config.security.oauth_access_token_expire_minutes,
        )

        return user, access_code
