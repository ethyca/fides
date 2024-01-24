from typing import Iterable, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def update_cors_middleware(
    app: FastAPI, allow_origins: Iterable[str], allow_origin_regex: str
) -> CORSMiddleware:
    """
    Update the CORSMiddleware of the running app with the provided origin parameters.

    Returns the _old_ middleware instance that is no longer being used.
    """
    existing_middleware = find_cors_middleware(app)
    app.user_middleware.remove(existing_middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_origin_regex=allow_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return existing_middleware


def find_cors_middleware(app: FastAPI) -> Optional[CORSMiddleware]:
    """Utility function to find the (first) cors middleware of the provided FastAPI app"""
    for mw in app.user_middleware:
        if mw.cls is CORSMiddleware:
            return mw
    return None
