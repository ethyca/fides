from typing import Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_respondent_email_verification import (
    FidesUserRespondentEmailVerification,
)

USER_NAME = "user_1"
PASSWORD = "test_password"
EMAIL_ADDRESS = "user_1@example.com"


@pytest.fixture
def user(db: Session) -> Generator[FidesUser, None, None]:
    user = FidesUser.create(
        db=db,
        data={"username": USER_NAME, "password": PASSWORD},
    )
    yield user
    user.delete(db)


@pytest.fixture
def respondent(db: Session) -> Generator[FidesUser, None, None]:
    user = FidesUser.create(
        db=db,
        data={
            "username": USER_NAME,
            "email_address": EMAIL_ADDRESS,
            "roles": ["respondent"],
        },
    )
    yield user
    user.delete(db)


@pytest.fixture
def external_respondent(db: Session) -> Generator[FidesUser, None, None]:
    user = FidesUser.create(
        db=db,
        data={
            "username": USER_NAME,
            "email_address": EMAIL_ADDRESS,
            "roles": ["external_respondent"],
        },
    )
    yield user
    user.delete(db)


@pytest.fixture
def system_manager(
    db: Session, user: FidesUser, system: System
) -> Generator[FidesUser, None, None]:
    user.set_as_system_manager(db, system)
    yield user


class TestCreateFidesUser:

    def test_create_user(self, db: Session) -> None:
        user = FidesUser.create(
            db=db,
            data={"username": USER_NAME, "password": PASSWORD},
        )

        assert user.username == USER_NAME
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.hashed_password != PASSWORD
        assert user.last_login_at is None
        assert user.password_reset_at is None

        assert not user.credentials_valid("bad_password")
        assert user.credentials_valid(PASSWORD)

        user.delete(db)

    def test_create_user_bad_payload(self, db: Session) -> None:
        with pytest.raises(KeyError):
            FidesUser.create(
                db=db,
                data={},
            )

    @pytest.mark.parametrize(
        "role, password_login_enabled",
        [
            ("approver", True),
            ("viewer", True),
            ("respondent", False),
            ("external_respondent", False),
        ],
    )
    def create_user_with_roles(
        self, db: Session, role: str, password_login_enabled: bool
    ) -> None:
        data = {
            "username": USER_NAME,
            "email_address": EMAIL_ADDRESS,
            "roles": [role],
        }
        if password_login_enabled:
            data["password"] = PASSWORD

        user = FidesUser.create(
            db=db,
            data=data,
        )

        assert user.username == USER_NAME
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.email_address == EMAIL_ADDRESS
        assert user.password_login_enabled is password_login_enabled
        if password_login_enabled:
            assert user.hashed_password is not None
        else:
            assert user.hashed_password is None

    @pytest.mark.parametrize("role", ["respondent", "external_respondent"])
    def create_user_with_roles_error_no_email(self, db: Session, role: str) -> None:
        data = {
            "username": USER_NAME,
            "roles": [role],
        }

        with pytest.raises(ValueError) as e:
            FidesUser.create(
                db=db,
                data=data,
            )

        assert "Email address is required for external respondents" in str(e.value)

    @pytest.mark.parametrize("role", ["respondent", "external_respondent"])
    def create_user_with_roles_error_password(self, db: Session, role: str) -> None:
        data = {
            "username": USER_NAME,
            "email_address": EMAIL_ADDRESS,
            "roles": [role],
            "password": PASSWORD,
        }

        with pytest.raises(ValueError) as e:
            FidesUser.create(
                db=db,
                data=data,
            )

        assert "Password login is not allowed for external respondents" in str(e.value)


class TestUpdateFidesUserPassword:
    def test_update_user_password(self, db: Session, user: FidesUser) -> None:
        user.update_password(db, "new_test_password")

        assert user.username == "user_1"
        assert user.password_reset_at is not None
        assert user.credentials_valid("new_test_password")
        assert user.hashed_password != "new_test_password"
        assert not user.credentials_valid("test_password")

        user.delete(db)

    def test_update_user_password_error_respondent(
        self, db: Session, respondent: FidesUser
    ) -> None:

        with pytest.raises(ValueError) as e:
            respondent.update_password(db, "new_test_password")

        assert "Password changes are not allowed for respondents" in str(e.value)


class TestUserSystemManager:
    def test_set_as_system_manager(
        self, db: Session, system: System, user: FidesUser
    ) -> None:
        user.set_as_system_manager(db, system)
        assert system in user.systems

    def test_set_as_system_manager_error_respondent(
        self, db: Session, system: System, respondent: FidesUser
    ) -> None:
        with pytest.raises(ValueError) as e:
            respondent.set_as_system_manager(db, system)

        assert "Respondents cannot be system managers." in str(e.value)

    def test_set_as_system_manager_error_system_manager(
        self, db: Session, system: System, system_manager: FidesUser
    ) -> None:
        with pytest.raises(ValueError) as e:
            system_manager.set_as_system_manager(db, system)

        assert "User 'user_1' is already a system manager of 'system_1'." in str(
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
        with pytest.raises(ValueError) as e:
            user.remove_as_system_manager(db, system)

        assert "User 'user_1' is not a manager of system 'system_1'." in str(e.value)


class TestUserProperties:
    def test_disabled_user(self, db: Session) -> None:
        user = FidesUser.create(
            db=db,
            data={
                "username": USER_NAME,
                "password": PASSWORD,
                "disabled": True,
                "disabled_reason": "test_reason",
            },
        )
        assert user.disabled
        assert user.disabled_reason == "test_reason"
        user.delete(db)

    def test_totp_secret(self, db: Session) -> None:
        user = FidesUser.create(
            db=db,
            data={
                "username": USER_NAME,
                "password": PASSWORD,
                "totp_secret": "test_secret",
            },
        )
        assert user.totp_secret == "test_secret"
        user.delete(db)

    def test_system_ids(
        self, db: Session, system_manager: FidesUser, system: System
    ) -> None:
        assert system.id in system_manager.system_ids

    def test_audit_logs_relationship(self, db: Session, user: FidesUser) -> None:
        # Test that audit_logs is a dynamic relationship
        assert hasattr(user.audit_logs, "filter")
        assert hasattr(user.audit_logs, "all")

    def test_client_relationship(self, db: Session) -> None:
        user = FidesUser.create(
            db=db,
            data={
                "username": USER_NAME,
                "password": PASSWORD,
            },
        )
        # Test that client relationship exists and is optional
        assert user.client is None
        user.delete(db)

    def test_permissions_relationship(self, db: Session, user: FidesUser) -> None:
        # Test that permissions relationship exists
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

    def test_password_reset_at(self, db: Session, user: FidesUser) -> None:
        assert user.password_reset_at is None
        user.update_password(db, "new_password")
        assert user.password_reset_at is not None

    def test_password_login_enabled(self, db: Session) -> None:
        # Test regular user
        user = FidesUser.create(
            db=db,
            data={
                "username": USER_NAME,
                "password": PASSWORD,
            },
        )
        assert user.password_login_enabled is None  # Default is None
        user.delete(db)

        # Test external respondent
        respondent = FidesUser.create(
            db=db,
            data={
                "username": USER_NAME,
                "email_address": EMAIL_ADDRESS,
                "roles": ["external_respondent"],
            },
        )
        assert respondent.password_login_enabled is False
        respondent.delete(db)
