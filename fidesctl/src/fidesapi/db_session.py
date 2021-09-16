from pathlib import Path
from typing import Callable, Optional

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session

from .sql_models.modelbase import SqlAlchemyBase

__factory: Optional[Callable[[], Session]] = None


def global_init(database_url: str):
    global __factory, __async_engine

    if __factory:
        return

    engine = sa.create_engine(database_url, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory

    if not __factory:
        raise Exception("You must call global_init() before using this method.")

    session: Session = __factory()
    session.expire_on_commit = False

    return session
