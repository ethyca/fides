import uuid
from datetime import datetime
from typing import Optional, Tuple

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.api.v1.endpoints.messaging_endpoints import user_email_invite_status
from fides.api.common_exceptions import AuthorizationError
from fides.api.models.client import ClientDetail
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_invite import FidesUserInvite
from fides.api.schemas.messaging.messaging import (
    MessagingActionType,
    UserInviteBodyParams,
)
from fides.api.schemas.redis_cache import Identity
from fides.api.service.messaging.message_dispatch_service import dispatch_message
from fides.config import FidesConfig
from fides.config.config_proxy import ConfigProxy


def invite_user(db: Session, config_proxy: ConfigProxy, user: FidesUser) -> None:
    """
    Generates a user invite and sends the invite code to the user via email.

    This is a no-op if email messaging isn't configured.
    """

    # invite user via email if email messaging is enabled and the Admin UI URL is defined
    if user_email_invite_status(db=db, config_proxy=config_proxy).enabled:
        invite_code = str(uuid.uuid4())
        FidesUserInvite.create(
            db=db, data={"username": user.username, "invite_code": invite_code}
        )
        user.update(db, data={"disabled": True})
        dispatch_message(
            db,
            action_type=MessagingActionType.USER_INVITE,
            to_identity=Identity(email=user.email_address),
            service_type=config_proxy.notifications.notification_service_type,
            message_body_params=UserInviteBodyParams(
                username=user.username, invite_code=invite_code
            ),
        )


def accept_invite(
    db: Session, config: FidesConfig, user: FidesUser, new_password: str
) -> Tuple[FidesUser, str]:
    """
    Updates the user password and enables the user. Also removes the user invite from the database.
    Returns a tuple of the updated user and their access code.
    """

    # update password and enable
    user.update_password(db=db, new_password=new_password)
    user.update(
        db,
        data={"disabled": False, "disabled_reason": None},
    )
    db.refresh(user)

    # delete invite
    if user.username:
        invite = FidesUserInvite.get_by(db=db, field="username", value=user.username)
        if invite:
            invite.delete(db)
    else:
        logger.warning("Username is missing, skipping invite deletion.")

    client = perform_login(
        db,
        config.security.oauth_client_id_length_bytes,
        config.security.oauth_client_secret_length_bytes,
        user,
    )

    logger.info("Creating login access token")
    access_code = client.create_access_code_jwe(config.security.app_encryption_key)

    return user, access_code


def perform_login(
    db: Session,
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
            db,
            client_id_byte_length,
            client_secret_byte_length,
            scopes=[],  # type: ignore
            roles=user.permissions.roles,  # type: ignore
            systems=user.system_ids,  # type: ignore
            user_id=user.id,
            in_memory=skip_save,  # If login flow has already errored, don't persist this to the database
        )
    else:
        # Refresh the client just in case - for example, scopes and roles were added via the db directly.
        client.roles = user.permissions.roles  # type: ignore
        client.systems = user.system_ids  # type: ignore
        if not skip_save:
            client.save(db)

    if user.permissions and (not user.permissions.roles and not user.systems):  # type: ignore
        logger.warning("User {} needs roles or systems to login.", user.id)
        raise AuthorizationError(detail="Not Authorized for this action")

    if not skip_save:
        user.last_login_at = datetime.utcnow()
        user.save(db)

    return client
