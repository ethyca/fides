"""
Sets up the database for use within the API.
"""

from typing import Callable, Optional

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session

FACTORY: Optional[Callable[[], Session]] = None
CURRENT_DATABASE_URL: str = ""


def global_init(database_url: str) -> None:
    """
    This runs once when the application first starts to
    set up the database connection and session factories.
    """
    global FACTORY  # pylint: disable=global-statement
    global CURRENT_DATABASE_URL  # pylint: disable=global-statement

    if FACTORY and CURRENT_DATABASE_URL == database_url:
        return

    engine = sa.create_engine(database_url, echo=False)
    FACTORY = orm.sessionmaker(bind=engine)
    CURRENT_DATABASE_URL = database_url


def create_session() -> Session:
    """
    Create and return a session for interacting with the database.
    """
    global FACTORY  # pylint: disable=global-statement

    if not FACTORY:
        raise Exception("You must call global_init() before using this method.")

    session: Session = FACTORY()
    session.expire_on_commit = False

    return session
