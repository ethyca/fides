from pathlib import Path

from fastapi import APIRouter

API_PREFIX = "/api/v1"
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
    return router.prefix.strip(API_PREFIX)
