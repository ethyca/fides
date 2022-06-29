"""One-time script to create the root user for the Admin UI"""

import getpass
from typing import List

from sqlalchemy.orm import Session

from fidesops.api.v1.scope_registry import CLIENT_CREATE, SCOPE_REGISTRY
from fidesops.common_exceptions import KeyOrNameAlreadyExists
from fidesops.core.config import config
from fidesops.db.database import init_db
from fidesops.db.session import get_db_session
from fidesops.models.client import ADMIN_UI_ROOT, ClientDetail
from fidesops.models.fidesops_user import FidesopsUser
from fidesops.models.fidesops_user_permissions import FidesopsUserPermissions
from fidesops.schemas.user import UserCreate
from fidesops.util.cryptographic_util import str_to_b64_str


def get_username(prompt: str) -> str:
    """Prompt the user for a username"""
    username = input(prompt)
    return username


def get_password(prompt: str) -> str:
    """Prompt the user for a password"""
    password = getpass.getpass(prompt)
    return str_to_b64_str(password)


def get_input(prompt: str) -> str:
    """
    Prompt the user for generic input.

    NB. This method is important to preserve so that
    our tests can effectively mock the `input` function
    and data that it returns.
    """
    return input(prompt)


def collect_username_and_password(db: Session) -> UserCreate:
    """Collect username and password information and validate"""
    username = get_username("Enter your username: ")
    first_name = get_input("Enter your first name: ")
    last_name = get_input("Enter your last name: ")
    password = get_password("Enter your password: ")
    verify_pass = get_password("Enter your password again: ")

    if password != verify_pass:
        raise Exception("Passwords do not match.")

    user_data = UserCreate(
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )
    user = FidesopsUser.get_by(db, field="username", value=user_data.username)

    if user:
        raise Exception(f"User with username '{username}' already exists.")

    return user_data


def create_user_and_client(db: Session) -> FidesopsUser:
    """One-time script to create the first user for the Admin UI"""
    if db.query(ClientDetail).filter_by(fides_key=ADMIN_UI_ROOT).first():
        raise KeyOrNameAlreadyExists("Admin UI Client already created.")

    user_data: UserCreate = collect_username_and_password(db)

    superuser = FidesopsUser.create(db=db, data=user_data.dict())

    scopes: List[str] = SCOPE_REGISTRY
    scopes.remove(CLIENT_CREATE)

    ClientDetail.create_client_and_secret(
        db, scopes, fides_key=ADMIN_UI_ROOT, user_id=superuser.id
    )

    FidesopsUserPermissions.create(
        db=db, data={"user_id": superuser.id, "scopes": scopes}
    )
    print(f"Superuser '{user_data.username}' created successfully!")
    return superuser


if __name__ == "__main__":
    init_db(config.database.SQLALCHEMY_DATABASE_URI)
    session_local = get_db_session()
    with session_local() as session:
        create_user_and_client(session)
