import zlib
from base64 import urlsafe_b64decode as b64d
from base64 import urlsafe_b64encode as b64e
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
    return router.prefix.replace(f"{API_PREFIX}/", "", 1)


def obscure(data: bytes) -> bytes:
    "obscures data as a minor security measure"
    return b64e(zlib.compress(data, 9))


def unobscure(obscured: bytes) -> bytes:
    "unobscures data as a minor security measure"
    return zlib.decompress(b64d(obscured))
