"""
Execution context for collecting log messages during privacy request processing.

Uses Python's contextvars for thread-safe, execution-scoped message collection.
"""

import contextvars
from contextlib import contextmanager
from typing import Generator, List, Optional

from loguru import logger

# Context variable for current execution messages
_execution_messages: contextvars.ContextVar[Optional[List[str]]] = (
    contextvars.ContextVar("execution_messages")
)


@contextmanager
def collect_execution_log_messages() -> Generator[List[str], None, None]:
    """
    Context manager for collecting execution log messages.

    Usage:
        with collect_execution_log_messages() as messages:
            # ... do work that calls add_execution_log_message()
            pass
        # messages now contains all collected messages

    Returns:
        List[str]: Messages collected during execution
    """
    messages: List[str] = []
    token = _execution_messages.set(messages)
    try:
        yield messages
    finally:
        _execution_messages.reset(token)


def add_execution_log_message(message: str) -> None:
    """Add a message to the current execution context"""
    try:
        messages = _execution_messages.get()
        if messages is not None and message.strip():
            messages.append(message.strip())
    except LookupError:
        logger.error(
            f"Attempted to call add_execution_log_message outside of execution context, unable to add message: {message}"
        )


def get_execution_log_messages() -> List[str]:
    """Get messages from current execution context (for testing/debugging)"""
    try:
        messages = _execution_messages.get()
        return messages.copy() if messages is not None else []
    except LookupError:
        return []
