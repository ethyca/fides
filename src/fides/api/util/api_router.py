from typing import Any, Callable

from fastapi import APIRouter as FastAPIRouter
from fastapi.types import DecoratedCallable


class APIRouter(FastAPIRouter):
    """
    Taken from: https://github.com/tiangolo/fastapi/issues/2060#issuecomment-834868906
    """

    def api_route(
        self, path: str, *, include_in_schema: bool = True, **kwargs: Any
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """
        Updated api_route function that automatically configures routes to have 2 versions.
        One without a trailing slash and another with it.
        """
        if path.endswith("/"):
            path = path[:-1]

        add_path = super().api_route(
            path, include_in_schema=include_in_schema, **kwargs
        )

        alternate_path = path + "/"
        add_alternate_path = super().api_route(
            alternate_path, include_in_schema=False, **kwargs
        )

        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            add_alternate_path(func)
            return add_path(func)

        return decorator

    def add_api_route(
        self, path: str, endpoint: Callable[..., Any], **kwargs: Any
    ) -> None:
        """
        Add an API route with automatic trailing slash handling.
        Registers both /path and /path/ versions.

        This handles direct calls to add_api_route() (not using decorators).
        """
        # Get include_in_schema from kwargs, default to True
        include_in_schema = kwargs.get("include_in_schema", True)

        # Normalize path to not have trailing slash
        if path.endswith("/"):
            path = path[:-1]

        # Add the main route (without trailing slash)
        super().add_api_route(path=path, endpoint=endpoint, **kwargs)

        # Add the alternate route (with trailing slash, hidden from schema)
        kwargs_alternate = kwargs.copy()
        kwargs_alternate["include_in_schema"] = False
        super().add_api_route(path=f"{path}/", endpoint=endpoint, **kwargs_alternate)
