"""
Sets up the database for use within the API.
"""

from typing import Callable, Optional

import sqlalchemy as sa
import sqlalchemy.orm as orm
from loguru import logger as log
from sqlalchemy.orm import Session

from fidesapi.errors import DatabaseUnavailableError

FACTORY: Optional[Callable[[], Session]] = None


def global_init(database_url: str) -> None:
    """
    This runs once when the application first starts to
    set up the database connection and session factories.
    """
    global FACTORY  # pylint: disable=global-statement

    if FACTORY:
        return

    engine = sa.create_engine(database_url, echo=False)
    FACTORY = orm.sessionmaker(bind=engine)


def create_session() -> Session:
    """
    Create and return a session for interacting with the database.
    """
    global FACTORY  # pylint: disable=global-statement

    if not FACTORY:
        raise DatabaseUnavailableError()

    log.debug("Creating database session")

    session: Session = FACTORY()
    session.expire_on_commit = False

    return session
