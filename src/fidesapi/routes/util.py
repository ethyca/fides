from pathlib import Path

from fastapi import APIRouter
from fidesctl.core.utils import API_PREFIX as _API_PREFIX

API_PREFIX = _API_PREFIX
WEBAPP_DIRECTORY = Path("src/fidesapi/build/static")
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
