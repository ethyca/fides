import asyncio
import logging
from asyncio import AbstractEventLoop
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Awaitable, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


executor = ThreadPoolExecutor(max_workers=2)


def _loop() -> AbstractEventLoop:
    """Return the event loop"""
    asyncio.set_event_loop(asyncio.SelectorEventLoop())
    return asyncio.get_event_loop()


def run_async(task: Callable[[Any], T], *args: Any) -> Awaitable[T]:
    """Run a callable async"""
    if not callable(task):
        raise TypeError("Task must be a callable")
    return _loop().run_in_executor(executor, task, *args)


def wait_for(t: Awaitable[T]) -> Optional[T]:
    """Wait for the return of a callable. This is mostly intended
    to be used for testing async tasks."""
    return asyncio.get_event_loop().run_until_complete(t)
