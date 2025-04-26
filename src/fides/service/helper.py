import functools
from typing import Any, Callable, Type, TypeVar
from fastapi import Depends, Request

T = TypeVar("T")


def Service(t: Type[T]) -> Any:
    def resolver(t: Type[T], request: Request) -> Callable[[], T]:
        return request.app.state.container

    return Depends(functools.partial(resolver, t))
