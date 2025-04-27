import functools
from typing import Any, Callable, Type, TypeVar
from fastapi import Request, Depends

T = TypeVar("T")


def resolver(t: Type[T], request: Request) -> Callable[[], T]:
    print("REsolving!!!!!!!!!!!!!!!!!!!!")
    asd = request.app.state.container.resolve(t)
    print("Resolved", asd)
    return asd


def Service(t: Type[T]) -> Any:  # noqa: N802
    print("mamamia", Depends)
    function = functools.partial(resolver, t)
    print("hmmmm", function)
    returns = Depends(function)
    print("wtf is ", returns, type(returns))
    return returns
