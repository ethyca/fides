import functools
import inspect
from typing import Annotated, Any, Callable, Optional, Type, TypeVar
from typing_extensions import Doc
from fastapi import Request, Depends
from fastapi import params

T = TypeVar("T")


def resolver(t: Type[T], request: Request) -> Callable[[], T]:
    print("REsolving!!!!!!!!!!!!!!!!!!!!")
    asd = request.app.state.container.resolve(t)
    print("Resolved", asd)
    return asd


def Service(
    t: Annotated[
        Optional[Callable[..., Any]],
        Doc(
            """
            A "dependable" callable (like a function).

            Don't call it directly, FastAPI will call it for you, just pass the object
            directly.
            """
        ),
    ] = None,
) -> Any:  # noqa: N802
    print("caller", print(inspect.stack()[1][3]))
    print("Depends fn", Depends)
    function = functools.partial(resolver, t)
    print("hmmmm", function)
    returns = Depends(function)
    print("wtf is ", returns, type(returns))
    return returns
