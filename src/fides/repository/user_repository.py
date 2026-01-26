"""
User repository module - data access layer for user operations.

This module provides a repository pattern for FidesUser database operations,
following the clean architecture principles of separating data access from
business logic.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Query, Session
from sqlalchemy_utils import escape_like

from fides.api.models.fides_user import FidesUser
from fides.api.schemas.user import DisabledReason
from fides.entities.user import UserEntity
from fides.repository.session import with_optional_session


class UserRepository:
    """
    Repository for FidesUser database operations.

    This repository handles all database interactions for users and returns
    session-independent UserEntity objects. Each method manages its own
    database session unless one is provided.
    """

    def _apply_deleted_filter(
        self, query: Query, include_deleted: bool = False
    ) -> Query:
        """Apply soft-delete filter to a query."""
        if not include_deleted:
            query = query.filter(FidesUser.deleted_at.is_(None))
        return query

    @with_optional_session
    def get_by_id(
        self,
        user_id: str,
        include_deleted: bool = False,
        session: Optional[Session] = None,
    ) -> Optional[UserEntity]:
        """
        Get user by ID, excluding soft-deleted users by default.

        Args:
            user_id: The user's unique identifier
            include_deleted: Whether to include soft-deleted users in results
            session: Optional database session (managed by decorator if not provided)

        Returns:
            UserEntity if found, None otherwise
        """
        assert session is not None
        query = session.query(FidesUser).filter(FidesUser.id == user_id)
        query = self._apply_deleted_filter(query, include_deleted)
        user = query.first()
        return UserEntity.model_validate(user) if user else None

    @with_optional_session
    def get_by_username(
        self,
        username: str,
        include_deleted: bool = False,
        session: Optional[Session] = None,
    ) -> Optional[UserEntity]:
        """
        Get user by username, excluding soft-deleted users by default.

        Args:
            username: The user's username
            include_deleted: Whether to include soft-deleted users in results
            session: Optional database session

        Returns:
            UserEntity if found, None otherwise
        """
        assert session is not None
        query = session.query(FidesUser).filter(FidesUser.username == username)
        query = self._apply_deleted_filter(query, include_deleted)
        user = query.first()
        return UserEntity.model_validate(user) if user else None

    @with_optional_session
    def get_by_email(
        self,
        email: str,
        include_deleted: bool = False,
        session: Optional[Session] = None,
    ) -> Optional[UserEntity]:
        """
        Get user by email address, excluding soft-deleted users by default.

        Args:
            email: The user's email address
            include_deleted: Whether to include soft-deleted users in results
            session: Optional database session

        Returns:
            UserEntity if found, None otherwise
        """
        assert session is not None
        query = session.query(FidesUser).filter(FidesUser.email_address == email)
        query = self._apply_deleted_filter(query, include_deleted)
        user = query.first()
        return UserEntity.model_validate(user) if user else None

    @with_optional_session
    def list_users(
        self,
        include_deleted: bool = False,
        username_filter: Optional[str] = None,
        session: Optional[Session] = None,
    ) -> List[UserEntity]:
        """
        List users with optional filters, excluding soft-deleted users by default.

        Args:
            include_deleted: Whether to include soft-deleted users in results
            username_filter: Optional username substring to filter by
            session: Optional database session

        Returns:
            List of UserEntity objects
        """
        assert session is not None
        query = session.query(FidesUser)
        query = self._apply_deleted_filter(query, include_deleted)

        if username_filter:
            query = query.filter(
                FidesUser.username.ilike(f"%{escape_like(username_filter)}%")
            )

        query = query.order_by(FidesUser.created_at.desc())
        users = query.all()
        return [UserEntity.model_validate(user) for user in users]

    def get_users_query(
        self,
        session: Session,
        include_deleted: bool = False,
    ) -> Query:
        """
        Get a base query for users with soft-delete filtering applied.

        This method returns a SQLAlchemy Query object that can be further
        filtered and paginated by the caller. Useful for pagination endpoints.

        Args:
            session: Database session
            include_deleted: Whether to include soft-deleted users

        Returns:
            SQLAlchemy Query object with soft-delete filter applied
        """
        query = session.query(FidesUser)
        return self._apply_deleted_filter(query, include_deleted)

    @with_optional_session
    def soft_delete(
        self,
        user_id: str,
        deleted_by_user_id: Optional[str] = None,
        session: Optional[Session] = None,
    ) -> Optional[UserEntity]:
        """
        Mark user as soft-deleted.

        Sets the deleted_at timestamp, deleted_by user ID, and disables the user
        to prevent any login attempts.

        Args:
            user_id: The user's unique identifier
            deleted_by_user_id: The ID of the user performing the deletion
            session: Optional database session

        Returns:
            The updated UserEntity, or None if user not found
        """
        assert session is not None
        user = session.query(FidesUser).filter(FidesUser.id == user_id).first()

        if not user:
            return None

        if user.is_deleted:
            logger.warning(f"User {user_id} is already deleted")
            return UserEntity.model_validate(user)

        user.deleted_at = datetime.now(timezone.utc)
        user.deleted_by = deleted_by_user_id
        user.disabled = True
        user.disabled_reason = DisabledReason.deleted

        session.add(user)

        logger.info(f"User {user_id} soft-deleted by {deleted_by_user_id}")
        return UserEntity.model_validate(user)

    @with_optional_session
    def get_orm_by_id(
        self,
        user_id: str,
        include_deleted: bool = False,
        session: Optional[Session] = None,
    ) -> Optional[FidesUser]:
        """
        Get the raw FidesUser ORM object by ID.

        This method is provided for cases where the ORM object is needed
        for operations that require database relationships or direct updates.
        Use with caution - prefer UserEntity for most use cases.

        Args:
            user_id: The user's unique identifier
            include_deleted: Whether to include soft-deleted users
            session: Optional database session

        Returns:
            FidesUser ORM object if found, None otherwise
        """
        assert session is not None
        query = session.query(FidesUser).filter(FidesUser.id == user_id)
        query = self._apply_deleted_filter(query, include_deleted)
        return query.first()

    @with_optional_session
    def get_orm_by_username(
        self,
        username: str,
        include_deleted: bool = False,
        session: Optional[Session] = None,
    ) -> Optional[FidesUser]:
        """
        Get the raw FidesUser ORM object by username.

        This method is provided for cases where the ORM object is needed
        for operations that require database relationships or direct updates.

        Args:
            username: The user's username
            include_deleted: Whether to include soft-deleted users
            session: Optional database session

        Returns:
            FidesUser ORM object if found, None otherwise
        """
        assert session is not None
        query = session.query(FidesUser).filter(FidesUser.username == username)
        query = self._apply_deleted_filter(query, include_deleted)
        return query.first()

    @with_optional_session
    def get_orm_by_email(
        self,
        email: str,
        include_deleted: bool = False,
        session: Optional[Session] = None,
    ) -> Optional[FidesUser]:
        """
        Get the raw FidesUser ORM object by email address.

        This method is provided for internal use when ORM object is needed.

        Args:
            email: The user's email address
            include_deleted: Whether to include soft-deleted users
            session: Optional database session

        Returns:
            FidesUser ORM object if found, None otherwise
        """
        assert session is not None
        query = session.query(FidesUser).filter(FidesUser.email_address == email)
        query = self._apply_deleted_filter(query, include_deleted)
        return query.first()

    @with_optional_session
    def update_user(
        self,
        user_id: str,
        data: Dict[str, Any],
        session: Optional[Session] = None,
    ) -> Optional[UserEntity]:
        """
        Update user fields.

        Args:
            user_id: The user's unique identifier
            data: Dictionary of fields to update
            session: Optional database session

        Returns:
            Updated UserEntity if found and not deleted, None otherwise
        """
        assert session is not None
        user = session.query(FidesUser).filter(FidesUser.id == user_id).first()

        if not user or user.is_deleted:
            return None

        user.update(session, data=data)
        return UserEntity.model_validate(user)

    @with_optional_session
    def update_password(
        self,
        user_id: str,
        new_password: str,
        session: Optional[Session] = None,
    ) -> Optional[UserEntity]:
        """
        Update user password.

        Args:
            user_id: The user's unique identifier
            new_password: The new password to set
            session: Optional database session

        Returns:
            Updated UserEntity if found and not deleted, None otherwise
        """
        assert session is not None
        user = session.query(FidesUser).filter(FidesUser.id == user_id).first()

        if not user or user.is_deleted:
            return None

        user.update_password(session, new_password=new_password)
        return UserEntity.model_validate(user)

    @with_optional_session
    def validate_credentials(
        self,
        user_id: str,
        password: str,
        encoding: str = "UTF-8",
        session: Optional[Session] = None,
    ) -> bool:
        """
        Validate user credentials.

        Args:
            user_id: The user's unique identifier
            password: The password to validate
            encoding: Password encoding (default UTF-8)
            session: Optional database session

        Returns:
            True if credentials are valid, False otherwise
        """
        assert session is not None
        user = session.query(FidesUser).filter(FidesUser.id == user_id).first()

        if not user or user.is_deleted:
            return False

        return user.credentials_valid(password, encoding)

    @with_optional_session
    def invalidate_user_client(
        self,
        user_id: str,
        session: Optional[Session] = None,
    ) -> bool:
        """
        Delete the user's OAuth client to invalidate all existing sessions.

        Args:
            user_id: The user's unique identifier
            session: Optional database session

        Returns:
            True if client was deleted, False if user not found or no client
        """
        assert session is not None
        user = session.query(FidesUser).filter(FidesUser.id == user_id).first()

        if not user or user.is_deleted:
            return False

        if user.client:
            try:
                user.client.delete(session)
                return True
            except Exception as exc:
                logger.exception(
                    "Unable to delete user client for user {}: {}",
                    user_id,
                    exc,
                )
                return False
        return False

    @with_optional_session
    def create_user(
        self,
        user_data: Dict[str, Any],
        session: Optional[Session] = None,
    ) -> UserEntity:
        """
        Create a new user.

        Args:
            user_data: Dictionary containing user creation data
            session: Optional database session

        Returns:
            The created UserEntity
        """
        assert session is not None
        user = FidesUser.create(db=session, data=user_data)
        return UserEntity.model_validate(user)
