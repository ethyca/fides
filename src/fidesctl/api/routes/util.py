from functools import update_wrapper
from pathlib import Path
from typing import Any, Callable

from fastapi import HTTPException, status

from fidesctl.api.utils.api_router import APIRouter
from fidesctl.core.utils import API_PREFIX as _API_PREFIX

API_PREFIX = _API_PREFIX
WEBAPP_DIRECTORY = Path("src/fidesctl/api/build/static")
WEBAPP_INDEX = WEBAPP_DIRECTORY / "index.html"


def get_resource_type(router: APIRouter) -> str:
    """
    Get the resource type from the prefix of an API router
    Args:
        router: Api router from which to extract the resource type

    Returns:
        The router's resource type
    """
    return router.prefix.replace(f"{API_PREFIX}/", "", 1)


def route_requires_aws_connector(func: Callable) -> Callable:
    """
    Function decorator raises a bad request http exception if
    required modules are not installed for the aws connector.
    """

    def wrapper_func(*args, **kwargs) -> Any:  # type: ignore
        try:
            import fidesctl.connectors.aws  # pylint: disable=unused-import
        except ModuleNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Packages not found, ensure aws is included: fidesctl[aws]",
            )
        return func(*args, **kwargs)

    return update_wrapper(wrapper_func, func)


def route_requires_okta_connector(func: Callable) -> Callable:
    """
    Function decorator raises a bad request http exception if
    required modules are not installed for the okta connector.
    """

    def wrapper_func(*args, **kwargs) -> Any:  # type: ignore
        try:
            import fidesctl.connectors.okta  # pylint: disable=unused-import
        except ModuleNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Packages not found, ensure aws is included: fidesctl[okta]",
            )
        return func(*args, **kwargs)

    return update_wrapper(wrapper_func, func)


def route_requires_bigquery_connector(func: Callable) -> Callable:
    """
    Function decorator raises a bad request http exception if
    required modules are not installed for the GCP BigQuery connector
    """

    def wrapper_func(*args, **kwargs) -> Any:  # type: ignore
        try:
            import fidesctl.connectors.bigquery  # pylint: disable=unused-import
        except ModuleNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Packages not found, ensure BigQuery is included: fidesctl[bigquery]",
            )
        return func(*args, **kwargs)

    return update_wrapper(wrapper_func, func)
