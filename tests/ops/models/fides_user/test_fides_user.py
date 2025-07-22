from typing import Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import SystemManagerException
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.models.fides_user_respondent_email_verification import (
    FidesUserRespondentEmailVerification,
)
from fides.api.models.sql_models import System


@pytest.fixture
def system_manager(
    db: Session, approver: FidesUser, system: System
) -> Generator[FidesUser, None, None]:
    approver.set_as_system_manager(db, system)
    yield approver


class TestCreateFidesUser:

    def test_create_user(self, db: Session, username: str, password: str) -> None:
        user = FidesUser.create(
            db=db,
            data={"username": username, "password": password},
        )

        assert user.username == username
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.hashed_password != password
        assert user.last_login_at is None
        assert user.password_reset_at is None

        assert not user.credentials_valid("bad_password")
        assert user.credentials_valid(password)

        user.delete(db)

    def test_create_user_bad_payload(self, db: Session) -> None:
        with pytest.raises(KeyError):
            FidesUser.create(
                db=db,
                data={},
            )

    def test_create_respondent(
        self, db: Session, username: str, email_address: str
    ) -> None:
        respondent = FidesUser.create_respondent(
            db=db,
            data={"username": username, "email_address": email_address},
        )
        assert respondent.username == username
        assert respondent.email_address == email_address

    def test_create_respondent_error_no_email(self, db: Session, username: str) -> None:
        with pytest.raises(ValueError) as e:
            FidesUser.create_respondent(
                db=db,
                data={"username": username},
            )
        assert "Email address is required for external respondents" in str(e.value)

    def test_create_respondent_error_password(
        self, db: Session, username: str, email_address: str, password: str
    ) -> None:
        with pytest.raises(ValueError) as e:
            FidesUser.create_respondent(
                db=db,
                data={
                    "username": username,
                    "email_address": email_address,
                    "password": password,
                },
            )
        assert "Password login is not allowed for external respondents" in str(e.value)


class TestUpdateFidesUserPassword:
    def test_update_user_password(self, db: Session, approver: FidesUser) -> None:
        approver.update_password(db, "new_test_password")

        assert approver.username == "user_1"
        assert approver.password_reset_at is not None
        assert approver.credentials_valid("new_test_password")
        assert approver.hashed_password != "new_test_password"
        assert not approver.credentials_valid("test_password")

    def test_update_user_password_external_respondent(
        self, db: Session, external_respondent: FidesUser
    ) -> None:

        with pytest.raises(ValueError) as e:
            external_respondent.update_password(db, "new_test_password")
        assert "Password changes are not allowed for external respondents" in str(
            e.value
        )


class TestUpdateFidesUserEmailAddress:
    def test_update_user_email_address(self, db: Session, approver: FidesUser) -> None:
        approver.update_email_address(db, "new_test_email@example.com")

        assert approver.email_address == "new_test_email@example.com"

    def test_update_user_email_address_error_external_respondent(
        self, db: Session, external_respondent: FidesUser
    ) -> None:
        with pytest.raises(ValueError) as e:
            external_respondent.update_email_address(db, "new_test_email@example.com")

        assert "Email address changes are not allowed for external respondents" in str(
            e.value
        )


class TestUserSystemManager:
    def test_set_as_system_manager(
        self, db: Session, system: System, approver: FidesUser
    ) -> None:
        approver.set_as_system_manager(db, system)
        assert system in approver.systems

    def test_set_as_system_manager_error_external_respondent(
        self, db: Session, system: System, external_respondent: FidesUser
    ) -> None:
        with pytest.raises(SystemManagerException) as e:
            external_respondent.set_as_system_manager(db, system)

        assert "External respondents cannot be system managers." in str(e.value)

    def test_set_as_system_manager_error_system_manager(
        self, db: Session, system: System, system_manager: FidesUser
    ) -> None:
        with pytest.raises(SystemManagerException) as e:
            system_manager.set_as_system_manager(db, system)

        assert f"User '{system_manager.username}' is already a system manager" in str(
            e.value
        )

    def test_remove_as_system_manager(
        self, db: Session, system: System, system_manager: FidesUser
    ) -> None:
        system_manager.remove_as_system_manager(db, system)
        assert system not in system_manager.systems

    def test_remove_as_system_manager_error(
        self, db: Session, system: System, user: FidesUser
    ) -> None:
        with pytest.raises(SystemManagerException) as e:
            user.remove_as_system_manager(db, system)

        assert f"User '{user.username}' is not a manager of system " in str(e.value)


class TestUserProperties:
    def test_disabled_user(self, db: Session, username: str, password: str) -> None:
        user = FidesUser.create(
            db=db,
            data={
                "username": username,
                "password": password,
                "disabled": True,
                "disabled_reason": "pending_invite",
            },
        )
        assert user.disabled
        assert user.disabled_reason.value == "pending_invite"
        user.delete(db)

    def test_system_ids(
        self, db: Session, system_manager: FidesUser, system: System
    ) -> None:
        assert system.id in system_manager.system_ids

    def test_audit_logs_relationship(self, db: Session, user: FidesUser) -> None:
        # Test that audit_logs is a dynamic relationship
        assert hasattr(user.audit_logs, "filter")
        assert hasattr(user.audit_logs, "all")

    def test_client_relationship(
        self, db: Session, username: str, password: str
    ) -> None:
        user = FidesUser.create(
            db=db,
            data={
                "username": username,
                "password": password,
            },
        )
        # Test that client relationship exists and is optional
        assert user.client is None
        user.delete(db)

    @pytest.mark.parametrize("user", ["approver", "respondent", "external_respondent"])
    def test_permissions_relationship(
        self, db: Session, user: FidesUser, request
    ) -> None:
        # Test that permissions relationship exists
        user = request.getfixturevalue(user)
        assert hasattr(user, "permissions")
        # Test that permissions is optional (can be None)
        assert user.permissions is not None

    def test_email_verifications_relationship(
        self, db: Session, external_respondent: FidesUser
    ) -> None:
        # Test that email_verifications is a dynamic relationship
        assert hasattr(external_respondent.email_verifications, "filter")
        assert hasattr(external_respondent.email_verifications, "all")

    def test_last_login_at(self, db: Session, user: FidesUser) -> None:
        assert user.last_login_at is None
        # This would typically be set by the login process
        # We're just testing the property exists and is nullable

    def test_password_reset_at(self, db: Session, approver: FidesUser) -> None:
        assert approver.password_reset_at is None
        approver.update_password(db, "new_password")
        assert approver.password_reset_at is not None

    def test_password_login_enabled(
        self, db: Session, username: str, email_address: str, password: str
    ) -> None:
        # Test regular user
        user = FidesUser.create(
            db=db,
            data={
                "username": username,
                "password": password,
            },
        )
        assert user.password_login_enabled is None  # Default is None
        user.delete(db)

        # Test external respondent
        respondent = FidesUser.create_respondent(
            db=db,
            data={
                "username": username,
                "email_address": email_address,
                "roles": ["external_respondent"],
            },
        )
        assert respondent.password_login_enabled is False
        respondent.delete(db)
