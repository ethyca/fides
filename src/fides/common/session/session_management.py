"""
Session management utilities for composable transaction boundaries.

These decorators allow repository/service methods to optionally receive
a database session. When no session is provided, the decorator creates one,
commits on success, and closes it. When a session is provided, the decorator
uses it and flushes (but does not commit), leaving commit control to the caller.
"""

from contextlib import AsyncExitStack, ExitStack
from functools import wraps
from typing import Any, Callable, Coroutine, Optional, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from fides.api.db.ctl_session import async_session
from fides.api.deps import get_autoclose_db_session

T = TypeVar("T")


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
