import functools
from typing import Annotated, Any, Callable, Optional, Type, TypeVar
from typing_extensions import Doc
from fastapi import Request, Depends

T = TypeVar("T")


def resolver(t: Type[T], request: Request) -> Callable[[], T]:
    return request.app.state.container.resolve(t)


def Service(
    t: Annotated[
        Optional[Callable[..., Any]],
        Doc(
            """
            A "Service" callable (like a function).

            Don't call it directly, since it wraps FastAPI's Depends, FastAPI will call it for you, just pass the object
            directly.
            """
        ),
    ] = None,
) -> T:
    return Depends(functools.partial(resolver, t))
