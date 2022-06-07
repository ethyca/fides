import zlib
from base64 import urlsafe_b64decode as b64d
from base64 import urlsafe_b64encode as b64e
from functools import update_wrapper
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, HTTPException, status

from fidesctl.connectors.models import AWSConfig, OktaConfig
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


def obscure_string(plaintext: str) -> str:
    "obscures a string as a minor security measure"

    return b64e(zlib.compress(plaintext.encode())).decode()


def unobscure_string(obscured: str) -> str:
    "unobscures a string as a minor security measure"
    return zlib.decompress(b64d(obscured.encode())).decode()


def unobscure_aws_config(aws_config: AWSConfig) -> AWSConfig:
    """
    Given an aws config unobscures the access key id and
    access key using the unobscure_string function.
    """
    unobscured_config = AWSConfig(
        region_name=aws_config.region_name,
        aws_access_key_id=unobscure_string(aws_config.aws_access_key_id),
        aws_secret_access_key=unobscure_string(aws_config.aws_secret_access_key),
    )
    return unobscured_config


def unobscure_okta_config(okta_config: OktaConfig) -> OktaConfig:
    """
    Given an okta config unobscures the token using the
    unobscure_string function.
    """
    unobscured_config = OktaConfig(
        orgUrl=okta_config.orgUrl, token=unobscure_string(okta_config.token)
    )
    return unobscured_config


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
