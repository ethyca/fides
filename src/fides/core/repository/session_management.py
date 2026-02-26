"""
Session management utilities for the service/repository layer.

Provides decorators that give methods composable session semantics:
- When called without a session, a new session is created, committed on
  success, and closed automatically.
- When called with an existing session, the method participates in the
  caller's transaction (flush only, no commit).

This allows service methods to be called standalone (from routes) or
composed together in a larger unit of work while sharing a single
transaction.
"""

from contextlib import AsyncExitStack, ExitStack
from functools import wraps
from typing import Any, Callable, Coroutine, Optional, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from fides.api.api.deps import (
    get_autoclose_db_session,
    get_readonly_autoclose_db_session,
)
from fides.api.db.ctl_session import async_session

T = TypeVar("T")


def with_optional_async_session(
    decorated_func: Callable[..., Coroutine[Any, Any, T]],
) -> Callable[..., Coroutine[Any, Any, T]]:
    """
    Decorator to handle optional async session management.

    If the decorated function receives session=None, creates a new session,
    commits, and closes it. If session is provided, uses it without committing/closing it.
    """

    @wraps(decorated_func)
    async def wrapper(
        self: Any, *args: Any, session: Optional[AsyncSession] = None, **kwargs: Any
    ) -> T:
        owns_session: bool
        result: T

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
    commits, and closes it. If session is provided, uses it without committing/closing it.
    """

    @wraps(decorated_func)
    def wrapper(
        self: Any, *args: Any, session: Optional[Session] = None, **kwargs: Any
    ) -> T:
        owns_session: bool
        result: T

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
        result: T

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
