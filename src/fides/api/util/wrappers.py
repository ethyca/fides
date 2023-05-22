import asyncio
from functools import wraps
from typing import Any, Callable


def sync(func: Callable) -> Any:
    """Converts an async function into a sync function."""

    @wraps(func)
    def wrap(*args: Any, **kwargs: Any) -> Any:
        try:
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(func(*args, **kwargs))
        except RuntimeError:
            return asyncio.run(func(*args, **kwargs))

    return wrap
