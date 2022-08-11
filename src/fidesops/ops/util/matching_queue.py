from __future__ import annotations

from typing import Callable, Generic, Optional, TypeVar

T = TypeVar("T")


class MatchingQueue(Generic[T]):
    """A basic LILO queue with the added ability to pop not only the head, but the first value matching a given input function."""

    def __init__(self, *values: T):
        self.data = list(values)

    def push(self, t: T) -> None:
        """insert into the queue"""
        self.data.append(t)

    def push_if_new(self, t: T) -> None:
        """insert into the queue only if this value is not already in the queue."""
        if t not in self.data:
            self.push(t)

    def pop(self) -> Optional[T]:
        """safely return the next value in the queue, or None if the queue is empty."""
        if self.data:
            v = self.data[0]
            del self.data[0]
            return v
        return None

    def pop_first_match(self, fn: Callable[[T], bool]) -> Optional[T]:
        """Find the first matching value for f and pop it or return None"""
        for idx, val in enumerate(self.data):
            if fn(val):
                del self.data[idx]
                return val
        # if no matching value exists, return None
        return None

    def is_empty(self) -> bool:
        """is the queue empty?"""
        return len(self.data) == 0

    def __repr__(self) -> str:
        return f"Queue {self.data}"
