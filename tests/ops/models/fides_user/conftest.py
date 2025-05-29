from typing import Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions

USERNAME = "user_1"
PASSWORD = "test_password"
EMAIL_ADDRESS = "user_1@example.com"


@pytest.fixture
def username() -> str:
    return USERNAME


@pytest.fixture
def password() -> str:
    return PASSWORD


@pytest.fixture
def email_address() -> str:
    return EMAIL_ADDRESS


@pytest.fixture
def user(db: Session, username: str, password: str) -> Generator[FidesUser, None, None]:
    user = FidesUser.create(
        db=db,
        data={"username": username, "password": password},
    )
    yield user
    user.delete(db)


@pytest.fixture
def respondent(db: Session) -> Generator[FidesUser, None, None]:
    user = FidesUser.create(
        db=db,
        data={
            "username": USERNAME,
            "email_address": EMAIL_ADDRESS,
            "roles": ["respondent"],
        },
    )
    FidesUserPermissions.create(
        db=db,
        data={"user_id": user.id, "roles": ["respondent"]},
    )
    yield user
    user.delete(db)


@pytest.fixture
def external_respondent(db: Session) -> Generator[FidesUser, None, None]:
    user = FidesUser.create(
        db=db,
        data={
            "username": USERNAME,
            "email_address": EMAIL_ADDRESS,
            "roles": ["external_respondent"],
        },
    )
    FidesUserPermissions.create(
        db=db,
        data={"user_id": user.id, "roles": ["external_respondent"]},
    )
    yield user
    user.delete(db)


@pytest.fixture
def approver(db: Session) -> Generator[FidesUser, None, None]:
    user = FidesUser.create(
        db=db,
        data={"username": USERNAME, "password": PASSWORD},
    )
    FidesUserPermissions.create(
        db=db,
        data={"user_id": user.id, "roles": ["approver"]},
    )
    yield user
    user.delete(db)
