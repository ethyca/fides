"""One-time script to create the root user for the Admin UI"""

import getpass
from typing import List

from fideslib.cryptography.cryptographic_util import str_to_b64_str
from fideslib.db.session import get_db_session
from fideslib.exceptions import KeyOrNameAlreadyExists
from fideslib.models.client import ADMIN_UI_ROOT, ClientDetail
from fideslib.models.fides_user import FidesUser
from fideslib.models.fides_user_permissions import FidesUserPermissions
from fideslib.oauth.schemas.user import UserCreate
from sqlalchemy.orm import Session

from fidesops.api.v1.scope_registry import CLIENT_CREATE, SCOPE_REGISTRY
from fidesops.core.config import config
from fidesops.db.database import init_db


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
    password = get_password(
        "Enter your password(minimum 8 characters, including 1 number, capital letter and symbol): "
    )
    verify_pass = get_password("Enter your password again: ")

    if password != verify_pass:
        raise Exception("Passwords do not match.")

    user_data = UserCreate(
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )
    user = FidesUser.get_by(db, field="username", value=user_data.username)

    if user:
        raise Exception(f"User with username '{username}' already exists.")

    return user_data


def create_user_and_client(db: Session) -> FidesUser:
    """One-time script to create the first user for the Admin UI"""
    if db.query(ClientDetail).filter_by(fides_key=ADMIN_UI_ROOT).first():
        raise KeyOrNameAlreadyExists("Admin UI Client already created.")

    user_data: UserCreate = collect_username_and_password(db)

    superuser = FidesUser.create(db=db, data=user_data.dict())

    scopes: List[str] = SCOPE_REGISTRY
    scopes.remove(CLIENT_CREATE)

    ClientDetail.create_client_and_secret(
        db,
        config.security.oauth_client_id_length_bytes,
        config.security.oauth_client_secret_length_bytes,
        scopes=scopes,
        fides_key=ADMIN_UI_ROOT,
        user_id=superuser.id,
    )

    FidesUserPermissions.create(db=db, data={"user_id": superuser.id, "scopes": scopes})
    print(f"Superuser '{user_data.username}' created successfully!")
    return superuser


if __name__ == "__main__":
    init_db(config.database.sqlalchemy_database_uri)
    session_local = get_db_session(config)
    with session_local() as session:
        create_user_and_client(session)
