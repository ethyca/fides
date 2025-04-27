import functools
from typing import Any, Callable, Type, TypeVar
from fastapi import Depends, Request

T = TypeVar("T")


def Service(t: Type[T]) -> Any:  # noqa: N802
    def resolver(t: Type[T], request: Request) -> Callable[[], T]:
        print("REsolving")
        asd = request.app.state.container.resolve(t)
        print("Resolved", asd)
        return asd

    print("mamamia")
    return Depends(functools.partial(resolver, t))
