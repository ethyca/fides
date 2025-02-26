from typing import Any, Iterable, Optional, Pattern

from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware

from fides.api.custom_types import URLOriginString


def update_cors_middleware(
    app: FastAPI,
    allow_origins: Iterable[URLOriginString],
    allow_origin_regex: Optional[Pattern[Any]],
) -> None:
    """
    Update the CORSMiddleware of the provided app with the provided origin parameters.

    In order to update CORSMiddleware after the app has already started, reversing the changes made here:
    https://github.com/encode/starlette/pull/2017/files
    """
    existing_middleware = find_cors_middleware(app)

    if existing_middleware:
        app.user_middleware.remove(existing_middleware)

    app.user_middleware.insert(
        0,
        Middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_origin_regex=allow_origin_regex,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    )
    # In more recent starlette versions, you cannot add middleware after an application has started.
    # We have an endpoint that lets us update cors origins. I'm largely attempting to restore the
    # behavior starlette was originally providing here.
    app.middleware_stack = app.build_middleware_stack()


def find_cors_middleware(app: FastAPI) -> Optional[Middleware]:
    """Utility function to find the (first) cors middleware of the provided FastAPI app"""
    for mw in app.user_middleware:
        if mw.cls is CORSMiddleware:
            return mw
    return None
