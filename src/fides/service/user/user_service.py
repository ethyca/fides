from typing_extensions import deprecated
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.api.v1.endpoints.messaging_endpoints import user_email_invite_status
from fides.api.common_exceptions import AuthorizationError
from fides.api.models.client import ClientDetail
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_invite import FidesUserInvite
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.oauth.roles import APPROVER, EXTERNAL_RESPONDENT, VIEWER
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy_utils import escape_like
from fides.api.schemas.messaging.messaging import (
    MessagingActionType,
    UserInviteBodyParams,
)
from fides.api.schemas.redis_cache import Identity
from fides.api.service.messaging.message_dispatch_service import dispatch_message
from fides.config import FidesConfig
from fides.config.config_proxy import ConfigProxy
from fides.entities.user import UserEntity
from fides.repository.user_repository import UserRepository
from fides.service.user.exceptions import (
    DeletedEmailError,
    DeletedUsernameError,
    EmailAlreadyExistsError,
    InvalidPasswordError,
    UserNotFoundError,
    UsernameAlreadyExistsError,
)


class UserService:
    """
    Service layer for user-related business logic.

    This service coordinates user operations and delegates data access
    to the UserRepository. Some methods still require a database session
    for operations involving related entities (invites, messaging, etc.).
    """

    def __init__(
        self,
        db: Session,
        config: FidesConfig,
        config_proxy: ConfigProxy,
        repository: Optional[UserRepository] = None,
    ):
        self.db = db
        self.config = config
        self.config_proxy = config_proxy
        self.repository = repository or UserRepository()

    def delete_user(
        self, user_id: str, deleted_by_user_id: Optional[str] = None
    ) -> Optional[UserEntity]:
        """
        Soft-delete a user.

        This marks the user as deleted without removing them from the database,
        preserving the user record for audit trails and historical references.
        Also invalidates any existing user sessions.

        Args:
            user_id: The ID of the user to delete
            deleted_by_user_id: The ID of the user performing the deletion

        Returns:
            The updated UserEntity, or None if user not found
        """
        deleted_user = self.repository.soft_delete(
            user_id=user_id,
            deleted_by_user_id=deleted_by_user_id,
            session=self.db,
        )

        if deleted_user:
            # Invalidate any existing sessions
            self.repository.invalidate_user_client(user_id=user_id, session=self.db)

        return deleted_user

    def get_user(
        self, user_id: str, include_deleted: bool = False
    ) -> Optional[UserEntity]:
        """
        Get a user by ID.

        Args:
            user_id: The user's unique identifier
            include_deleted: Whether to include soft-deleted users

        Returns:
            UserEntity if found, None otherwise
        """
        return self.repository.get_by_id(
            user_id=user_id,
            include_deleted=include_deleted,
            session=self.db,
        )

    def get_user_by_username(
        self, username: str, include_deleted: bool = False
    ) -> Optional[UserEntity]:
        """
        Get a user by username.

        Args:
            username: The user's username
            include_deleted: Whether to include soft-deleted users

        Returns:
            UserEntity if found, None otherwise
        """
        return self.repository.get_by_username(
            username=username,
            include_deleted=include_deleted,
            session=self.db,
        )

    def get_user_by_email(
        self, email: str, include_deleted: bool = False
    ) -> Optional[UserEntity]:
        """
        Get a user by email address.

        Args:
            email: The user's email address
            include_deleted: Whether to include soft-deleted users

        Returns:
            UserEntity if found, None otherwise
        """
        return self.repository.get_by_email(
            email=email,
            include_deleted=include_deleted,
            session=self.db,
        )

    @deprecated("Refactor the calling function to not use ORM objects")
    def get_user_orm(self, user_id: str) -> Optional[FidesUser]:
        """
        Get user ORM object by ID, excluding soft-deleted users.

        This method provides ORM access for legacy code that needs to access
        user relationships (permissions, client, systems). New code should
        prefer using UserEntity-based methods where possible.

        Args:
            user_id: The user's unique identifier

        Returns:
            FidesUser ORM object if found and not deleted, None otherwise
        """
        return self.repository.get_orm_by_id(
            user_id=user_id, include_deleted=False, session=self.db
        )

    @deprecated("Refactor the calling function to not use ORM objects")
    def get_user_orm_by_username(
        self, username: str, include_deleted: bool = False
    ) -> Optional[FidesUser]:
        """
        Get user ORM object by username.

        This method provides ORM access for legacy code that needs to access
        user relationships (permissions, client, systems). New code should
        prefer using UserEntity-based methods where possible.

        Args:
            username: The user's username
            include_deleted: Whether to include soft-deleted users (needed for login flows)

        Returns:
            FidesUser ORM object if found, None otherwise
        """
        return self.repository.get_orm_by_username(
            username=username, include_deleted=include_deleted, session=self.db
        )

    def update_user(
        self, user_id: str, data: Dict[str, Any]
    ) -> Optional[UserEntity]:
        """
        Update a user's profile data.

        Args:
            user_id: The user's unique identifier
            data: Dictionary of fields to update

        Returns:
            Updated UserEntity if found and not deleted, None otherwise
        """
        return self.repository.update_user(
            user_id=user_id,
            data=data,
            session=self.db,
        )

    def update_password(self, user_id: str, new_password: str) -> Optional[UserEntity]:
        """
        Update a user's password (for admin/force reset).

        Invalidates all existing user sessions after password change.

        Args:
            user_id: The user's unique identifier
            new_password: The new password to set

        Returns:
            Updated UserEntity if found and not deleted, None otherwise
        """
        updated = self.repository.update_password(
            user_id=user_id,
            new_password=new_password,
            session=self.db,
        )
        if updated:
            self.repository.invalidate_user_client(user_id=user_id, session=self.db)
        return updated

    def self_update_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str,
    ) -> UserEntity:
        """
        User-initiated password change with old password validation.

        Args:
            user_id: The user's unique identifier
            old_password: The current password for validation
            new_password: The new password to set

        Returns:
            Updated UserEntity

        Raises:
            UserNotFoundError: If user not found or is deleted
            InvalidPasswordError: If old password is incorrect
        """
        # Validate old password
        if not self.repository.validate_credentials(
            user_id=user_id,
            password=old_password,
            encoding=self.config.security.encoding,
            session=self.db,
        ):
            # Check if user exists at all
            user = self.repository.get_by_id(user_id=user_id, session=self.db)
            if not user:
                raise UserNotFoundError(f"User with id {user_id} not found.")
            raise InvalidPasswordError("Incorrect password.")

        # Update password
        updated = self.repository.update_password(
            user_id=user_id,
            new_password=new_password,
            session=self.db,
        )
        if not updated:
            raise UserNotFoundError(f"User with id {user_id} not found.")

        # Invalidate sessions
        self.repository.invalidate_user_client(user_id=user_id, session=self.db)

        return updated

    def user_exists(self, user_id: str) -> bool:
        """
        Check if an active (non-deleted) user exists.

        Args:
            user_id: The user's unique identifier

        Returns:
            True if user exists and is not deleted, False otherwise
        """
        return self.repository.get_by_id(user_id=user_id, session=self.db) is not None

    def user_exists_by_username(self, username: str) -> bool:
        """
        Check if an active user exists by username.

        Args:
            username: The user's username

        Returns:
            True if user exists and is not deleted, False otherwise
        """
        return (
            self.repository.get_by_username(username=username, session=self.db)
            is not None
        )

    def get_users_paginated(
        self,
        params: Any,
        username_filter: Optional[str] = None,
        include_external: bool = True,
        exclude_approvers: bool = False,
        restrict_to_user_id: Optional[str] = None,
    ) -> Any:
        """
        Get a paginated list of users with filtering.

        Args:
            params: Pagination parameters (fastapi-pagination Params)
            username_filter: Optional username substring to filter by
            include_external: Whether to include external respondents
            exclude_approvers: Whether to exclude approvers
            restrict_to_user_id: If set, only return this specific user (for USER_READ_OWN)

        Returns:
            Paginated list of users
        """
        query = self.repository.get_users_query(session=self.db, include_deleted=False)

        # If restricted to a specific user (USER_READ_OWN scope)
        if restrict_to_user_id:
            query = query.filter(FidesUser.id == restrict_to_user_id)

        # Apply username filter
        if username_filter:
            query = query.filter(
                FidesUser.username.ilike(f"%{escape_like(username_filter)}%")
            )

        # Apply role-based filters
        if not include_external or exclude_approvers:
            query = query.join(FidesUserPermissions)
            if not include_external:
                query = query.filter(
                    ~FidesUserPermissions.roles.op("@>")([EXTERNAL_RESPONDENT])
                )
            if exclude_approvers:
                query = query.filter(~FidesUserPermissions.roles.op("@>")([APPROVER]))

        return paginate(query.order_by(FidesUser.created_at.desc()), params=params)

    def create_user(self, user_data: Dict[str, Any]) -> UserEntity:
        """
        Create a new user with validation.

        Validates that the username and email are not already in use
        (including by soft-deleted users), creates the user with default
        permissions, and sends an invitation email if configured.

        Args:
            user_data: Dictionary containing user creation data
                (username, password, email_address, first_name, last_name, etc.)

        Returns:
            The created UserEntity

        Raises:
            UsernameAlreadyExistsError: If username is already taken by an active user
            DeletedUsernameError: If username belongs to a soft-deleted user
            EmailAlreadyExistsError: If email is already taken by an active user
            DeletedEmailError: If email belongs to a soft-deleted user
        """
        username = user_data.get("username")
        email_address = user_data.get("email_address")

        # Check if username is the root username
        if (
            self.config_proxy.security.root_username
            and self.config_proxy.security.root_username == username
        ):
            raise UsernameAlreadyExistsError("Username already exists.")

        # Check for existing user with same username (include deleted to check for conflicts)
        existing_user = self.repository.get_by_username(
            username=username, include_deleted=True, session=self.db
        )
        if existing_user:
            if existing_user.is_deleted:
                raise DeletedUsernameError(
                    "This username belongs to a deleted user and cannot be reused."
                )
            raise UsernameAlreadyExistsError("Username already exists.")

        # Check for existing user with same email (include deleted to check for conflicts)
        if email_address:
            existing_email_user = self.repository.get_by_email(
                email=email_address, include_deleted=True, session=self.db
            )
            if existing_email_user:
                if existing_email_user.is_deleted:
                    raise DeletedEmailError(
                        "This email address belongs to a deleted user and cannot be reused."
                    )
                raise EmailAlreadyExistsError(
                    "User with this email address already exists."
                )

        # Create the user via repository
        user_entity = self.repository.create_user(user_data=user_data, session=self.db)

        # Send invitation email if configured (may be overridden by subclasses)
        self.invite_user(user_entity)

        logger.info("Created user with id: '{}'.", user_entity.id)

        # Create default permissions
        FidesUserPermissions.create(
            db=self.db,
            data={"user_id": user_entity.id, "roles": [VIEWER]},
        )

        return user_entity

    def invite_user(self, user: UserEntity) -> None:
        """
        Generates a user invite and sends the invite code to the user via email.

        This is a no-op if email messaging isn't configured.

        Args:
            user: The UserEntity of the user to invite
        """
        if not user_email_invite_status(
            db=self.db, config_proxy=self.config_proxy
        ).enabled:
            logger.debug(
                "Skipping invitation email, an email messaging provider is not enabled",
            )
            return

        invite_code = str(uuid.uuid4())
        FidesUserInvite.create(
            db=self.db,
            data={"username": user.username, "invite_code": invite_code},
        )
        # Disable user until they accept invite
        self.repository.update_user(
            user_id=user.id, data={"disabled": True}, session=self.db
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
                user_id=user.id,
                in_memory=skip_save,  # If login flow has already errored, don't persist this to the database
            )
        else:
            # Refresh the client just in case - for example, scopes and roles were added via the db directly.
            client.roles = user.permissions.roles  # type: ignore
            client.systems = user.system_ids  # type: ignore
            if not skip_save:
                client.save(self.db)

        if user.permissions and (not user.permissions.roles and not user.systems):  # type: ignore
            logger.warning("User {} needs roles or systems to login.", user.id)
            raise AuthorizationError(detail="Not Authorized for this action")

        if not skip_save:
            user.last_login_at = datetime.now(timezone.utc)
            user.save(self.db)

        return client

    def accept_invite_by_username(
        self, username: str, new_password: str
    ) -> Tuple[UserEntity, str]:
        """
        Accept a user invitation by username.

        Looks up the user by username, updates their password, enables them,
        removes the invite, and performs login.

        Args:
            username: The username of the invited user
            new_password: The new password to set

        Returns:
            Tuple of (UserEntity, access_code)

        Raises:
            UserNotFoundError: If user not found or is deleted
        """
        user = self.repository.get_orm_by_username(
            username=username, include_deleted=False, session=self.db
        )
        if not user:
            raise UserNotFoundError(f"User with username {username} does not exist.")

        # Update password and enable
        user.update_password(db=self.db, new_password=new_password)
        user.update(
            self.db,
            data={"disabled": False, "disabled_reason": None},
        )
        self.db.refresh(user)

        # Delete invite
        invite = FidesUserInvite.get_by(db=self.db, field="username", value=username)
        if invite:
            invite.delete(self.db)

        client = self.perform_login(
            self.config.security.oauth_client_id_length_bytes,
            self.config.security.oauth_client_secret_length_bytes,
            user,
        )

        logger.info("Creating login access token")
        access_code = client.create_access_code_jwe(
            self.config.security.app_encryption_key
        )

        return UserEntity.model_validate(user), access_code
