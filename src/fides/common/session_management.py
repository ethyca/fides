"""
Session management utilities for composable transaction boundaries.

These decorators allow repository/service methods to optionally receive
a database session. When no session is provided, the decorator creates one,
commits on success, and closes it. When a session is provided, the decorator
uses it and flushes (but does not commit), leaving commit control to the caller.
"""

from contextlib import AsyncExitStack, ExitStack, contextmanager
from functools import wraps
from typing import Any, Callable, Coroutine, Generator, Optional, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from fides.api.db.ctl_session import async_session
from fides.api.db.session import get_db_engine, get_db_session
from fides.config import CONFIG

T = TypeVar("T")

_engine = None


def get_api_session() -> Session:
    """Create a database session using a module-level engine singleton."""
    global _engine  # pylint: disable=W0603
    if not _engine:
        _engine = get_db_engine(
            config=CONFIG,
            pool_size=CONFIG.database.api_engine_pool_size,
            max_overflow=CONFIG.database.api_engine_max_overflow,
            keepalives_idle=CONFIG.database.api_engine_keepalives_idle,
            keepalives_interval=CONFIG.database.api_engine_keepalives_interval,
            keepalives_count=CONFIG.database.api_engine_keepalives_count,
            pool_pre_ping=CONFIG.database.api_engine_pool_pre_ping,
        )
    SessionLocal = get_db_session(CONFIG, engine=_engine)
    return SessionLocal()


def get_db() -> Generator[Session, None, None]:
    """Return a database session as a FastAPI-compatible dependency generator."""
    try:
        db = get_api_session()
        yield db
    finally:
        db.close()


@contextmanager
def get_autoclose_db_session() -> Generator[Session, None, None]:
    """
    Return a database session as a context manager that automatically closes
    when the context exits.

    Use this when you need manual control over the session lifecycle
    outside of API endpoints.
    """
    try:
        db = get_api_session()
        yield db
    finally:
        db.close()


def with_optional_async_session(
    decorated_func: Callable[..., Coroutine[Any, Any, T]],
) -> Callable[..., Coroutine[Any, Any, T]]:
    """
    Decorator to handle optional async session management.

    If the decorated function receives session=None, creates a new session,
    commits, and closes it. If session is provided, uses it without
    committing/closing it.
    """

    @wraps(decorated_func)
    async def wrapper(
        self: Any, *args: Any, session: Optional[AsyncSession] = None, **kwargs: Any
    ) -> T:
        async with AsyncExitStack() as stack:
            if not session:
                db_session: AsyncSession = await stack.enter_async_context(
                    async_session()
                )
                owns_session = True
            else:
                db_session = session
                owns_session = False

            result = await decorated_func(self, *args, session=db_session, **kwargs)

            if owns_session:
                await db_session.commit()
            else:
                await db_session.flush()

        return result

    return wrapper


def with_optional_sync_session(decorated_func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle optional sync session management.

    If the decorated function receives session=None, creates a new session,
    commits, and closes it. If session is provided, uses it without
    committing/closing it.
    """

    @wraps(decorated_func)
    def wrapper(
        self: Any, *args: Any, session: Optional[Session] = None, **kwargs: Any
    ) -> T:
        with ExitStack() as stack:
            if not session:
                db_session: Session = stack.enter_context(get_autoclose_db_session())
                owns_session = True
            else:
                db_session = session
                owns_session = False

            result = decorated_func(self, *args, session=db_session, **kwargs)

            if owns_session:
                db_session.commit()
            else:
                db_session.flush()

        return result

    return wrapper


_readonly_engine = None


def get_readonly_api_session() -> Session:
    """Create a read-only database session using a module-level engine singleton.

    Falls back to the primary database session if no read-only URI is configured.
    """
    if not CONFIG.database.sqlalchemy_readonly_database_uri:
        return get_api_session()

    global _readonly_engine  # pylint: disable=W0603
    if not _readonly_engine:
        _readonly_engine = get_db_engine(
            database_uri=CONFIG.database.sqlalchemy_readonly_database_uri,
            pool_size=CONFIG.database.api_engine_pool_size,
            max_overflow=CONFIG.database.api_engine_max_overflow,
            keepalives_idle=CONFIG.database.api_engine_keepalives_idle,
            keepalives_interval=CONFIG.database.api_engine_keepalives_interval,
            keepalives_count=CONFIG.database.api_engine_keepalives_count,
            pool_pre_ping=CONFIG.database.api_engine_pool_pre_ping,
        )
    SessionLocal = get_db_session(CONFIG, engine=_readonly_engine)
    return SessionLocal()


@contextmanager
def get_readonly_autoclose_db_session() -> Generator[Session, None, None]:
    """
    Return a read-only database session as a context manager that automatically
    closes when the context exits. Falls back to the primary database session
    if read-only is not configured.

    Use this when you need manual control over the session lifecycle
    outside of API endpoints.
    """
    if not CONFIG.database.sqlalchemy_readonly_database_uri:
        with get_autoclose_db_session() as db:
            yield db
        return

    try:
        db = get_readonly_api_session()
        yield db
    finally:
        db.close()


def with_optional_sync_readonly_session(
    decorated_func: Callable[..., T],
) -> Callable[..., T]:
    """
    Read-only variant of ``with_optional_sync_session``.

    When the decorated function is called without a session, a read-only
    session (backed by the reader DB engine when configured) is created and
    closed automatically.  No commit or flush is performed because the
    caller should not be mutating data.

    When a session is provided (e.g. the method is called from a write
    context that already holds a session), that session is used as-is.
    """

    @wraps(decorated_func)
    def wrapper(
        self: Any, *args: Any, session: Optional[Session] = None, **kwargs: Any
    ) -> T:
        with ExitStack() as stack:
            if not session:
                db_session: Session = stack.enter_context(
                    get_readonly_autoclose_db_session()
                )
            else:
                db_session = session

            result = decorated_func(self, *args, session=db_session, **kwargs)

        return result

    return wrapper
