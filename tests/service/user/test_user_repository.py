"""Tests for the UserRepository class."""

from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from fides.api.cryptography.cryptographic_util import str_to_b64_str
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.oauth.roles import VIEWER
from fides.api.schemas.user import DisabledReason
from fides.repository.user_repository import UserRepository


class TestUserRepository:
    """Tests for the UserRepository class."""

    @pytest.fixture
    def repository(self) -> UserRepository:
        """Create a UserRepository instance."""
        return UserRepository()

    @pytest.fixture
    def test_user(self, db: Session) -> FidesUser:
        """Create a test user for testing."""
        user = FidesUser.create(
            db=db,
            data={
                "username": "test_repository_user",
                "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
                "email_address": "test.repo.user@example.com",
            },
        )
        FidesUserPermissions.create(db=db, data={"user_id": user.id, "roles": [VIEWER]})
        return user

    def test_get_by_id(
        self, repository: UserRepository, test_user: FidesUser, db: Session
    ) -> None:
        """Test getting a user by ID."""
        entity = repository.get_by_id(test_user.id, session=db)

        assert entity is not None
        assert entity.id == test_user.id
        assert entity.username == test_user.username
        assert entity.email_address == test_user.email_address

    def test_get_by_id_not_found(self, repository: UserRepository, db: Session) -> None:
        """Test getting a non-existent user by ID."""
        entity = repository.get_by_id("nonexistent_id", session=db)
        assert entity is None

    def test_get_by_username(
        self, repository: UserRepository, test_user: FidesUser, db: Session
    ) -> None:
        """Test getting a user by username."""
        entity = repository.get_by_username(test_user.username, session=db)

        assert entity is not None
        assert entity.id == test_user.id
        assert entity.username == test_user.username

    def test_get_by_email(
        self, repository: UserRepository, test_user: FidesUser, db: Session
    ) -> None:
        """Test getting a user by email."""
        entity = repository.get_by_email(test_user.email_address, session=db)

        assert entity is not None
        assert entity.id == test_user.id
        assert entity.email_address == test_user.email_address

    def test_list_users(
        self, repository: UserRepository, test_user: FidesUser, db: Session
    ) -> None:
        """Test listing users."""
        entities = repository.list_users(session=db)

        assert len(entities) >= 1
        user_ids = [e.id for e in entities]
        assert test_user.id in user_ids

    def test_list_users_with_username_filter(
        self, repository: UserRepository, test_user: FidesUser, db: Session
    ) -> None:
        """Test listing users with a username filter."""
        entities = repository.list_users(
            username_filter="test_repository", session=db
        )

        assert len(entities) >= 1
        for entity in entities:
            assert "test_repository" in entity.username.lower()

    def test_soft_delete(
        self, repository: UserRepository, test_user: FidesUser, db: Session
    ) -> None:
        """Test soft-deleting a user."""
        deleted_user = repository.soft_delete(
            user_id=test_user.id,
            deleted_by_user_id="admin_user_id",
            session=db,
        )

        assert deleted_user is not None
        assert deleted_user.is_deleted is True
        assert deleted_user.deleted_at is not None
        assert deleted_user.deleted_by == "admin_user_id"
        assert deleted_user.disabled is True
        assert deleted_user.disabled_reason == DisabledReason.deleted.value

        # Verify the user is updated in the database
        db.refresh(test_user)
        assert test_user.deleted_at is not None
        assert test_user.deleted_by == "admin_user_id"
        assert test_user.disabled is True
        assert test_user.disabled_reason == DisabledReason.deleted

    def test_soft_delete_excludes_from_queries(
        self, repository: UserRepository, test_user: FidesUser, db: Session
    ) -> None:
        """Test that soft-deleted users are excluded from queries by default."""
        # Soft-delete the user
        repository.soft_delete(
            user_id=test_user.id,
            deleted_by_user_id="admin_user_id",
            session=db,
        )
        db.commit()

        # User should not be found with default include_deleted=False
        entity = repository.get_by_id(test_user.id, include_deleted=False, session=db)
        assert entity is None

        entity = repository.get_by_username(
            test_user.username, include_deleted=False, session=db
        )
        assert entity is None

        entity = repository.get_by_email(
            test_user.email_address, include_deleted=False, session=db
        )
        assert entity is None

        # User should not appear in list
        entities = repository.list_users(include_deleted=False, session=db)
        user_ids = [e.id for e in entities]
        assert test_user.id not in user_ids

    def test_include_deleted_users(
        self, repository: UserRepository, test_user: FidesUser, db: Session
    ) -> None:
        """Test that soft-deleted users can be retrieved with include_deleted=True."""
        # Soft-delete the user
        repository.soft_delete(
            user_id=test_user.id,
            deleted_by_user_id="admin_user_id",
            session=db,
        )
        db.commit()

        # User should be found with include_deleted=True
        entity = repository.get_by_id(test_user.id, include_deleted=True, session=db)
        assert entity is not None
        assert entity.id == test_user.id
        assert entity.is_deleted is True

        entity = repository.get_by_username(
            test_user.username, include_deleted=True, session=db
        )
        assert entity is not None

        entity = repository.get_by_email(
            test_user.email_address, include_deleted=True, session=db
        )
        assert entity is not None

        # User should appear in list with include_deleted=True
        entities = repository.list_users(include_deleted=True, session=db)
        user_ids = [e.id for e in entities]
        assert test_user.id in user_ids

    def test_soft_delete_nonexistent_user(
        self, repository: UserRepository, db: Session
    ) -> None:
        """Test soft-deleting a non-existent user returns None."""
        result = repository.soft_delete(
            user_id="nonexistent_id",
            deleted_by_user_id="admin_user_id",
            session=db,
        )
        assert result is None

    def test_soft_delete_already_deleted_user(
        self, repository: UserRepository, test_user: FidesUser, db: Session
    ) -> None:
        """Test that soft-deleting an already deleted user is idempotent."""
        # First deletion
        repository.soft_delete(
            user_id=test_user.id,
            deleted_by_user_id="admin_user_id",
            session=db,
        )
        db.commit()
        db.refresh(test_user)
        first_deleted_at = test_user.deleted_at

        # Second deletion (should not change deleted_at)
        result = repository.soft_delete(
            user_id=test_user.id,
            deleted_by_user_id="another_admin_id",
            session=db,
        )

        assert result is not None
        assert result.is_deleted is True
        # The deleted_at should remain the same from the first deletion
        db.refresh(test_user)
        assert test_user.deleted_at == first_deleted_at
