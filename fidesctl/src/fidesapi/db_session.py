from typing import Callable, Optional

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session

__factory: Optional[Callable[[], Session]] = None


def global_init(database_url: str):
    """
    This runs once when the application first starts to
    set up the database connection and session factories.
    """
    global __factory

    if __factory:
        return

    engine = sa.create_engine(database_url, echo=False)
    __factory = orm.sessionmaker(bind=engine)


def create_session() -> Session:
    global __factory

    if not __factory:
        raise Exception("You must call global_init() before using this method.")

    session: Session = __factory()
    session.expire_on_commit = False

    return session
