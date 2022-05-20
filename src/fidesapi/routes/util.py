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


def obscure_string(plaintext: str) -> str:
    "obscures a string as a minor security measure"

    return b64e(zlib.compress(plaintext_string.encode())).decode()


def unobscure_string(obscured: str) -> str:
    "unobscures a string as a minor security measure"
    return zlib.decompress(b64d(obscured_string.encode())).decode()
