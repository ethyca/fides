"""
Session management utilities for the repository layer.
"""

from contextlib import ExitStack
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from sqlalchemy.orm import Session

from fides.api.api.deps import get_autoclose_db_session

T = TypeVar("T")


def with_optional_session(decorated_func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle optional sync session management.

    If the decorated function receives session=None, creates a new session,
    commits, and closes it. If session is provided, uses it without committing/closing.

    Usage:
        @with_optional_session
        def my_repository_method(self, ..., session: Optional[Session] = None) -> T:
            assert session is not None
            # session is guaranteed to be a valid Session here
            ...
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
