from typing import Dict

import requests
from loguru import logger

from fides.api.ops.api.v1 import urn_registry as urls
from fides.core.config import CONFIG

from . import constants


def create_user(
    auth_header: Dict[str, str],
    username=constants.FIDES_USERNAME,
    password=constants.FIDES_PASSWORD,
):
    """Adds a user with full permissions - all scopes and admin role"""
    login_response = requests.post(
        f"{constants.BASE_URL}{urls.LOGIN}",
        headers=auth_header,
        json={
            "username": username,
            "password": password,
        },
    )

    if login_response.ok:
        logger.info(f"Successfully logged in as {username}")
        return

    response = requests.post(
        f"{constants.BASE_URL}{urls.USERS}",
        headers=auth_header,
        json={
            "first_name": "Atest",
            "last_name": "User",
            "username": username,
            "password": password,
        },
    )

    if not response.ok:
        raise RuntimeError(
            f"fides user creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )

    user_id = response.json()["id"]

    user_permissions_url = urls.USER_PERMISSIONS.format(user_id=user_id)
    response = requests.put(
        f"{constants.BASE_URL}{user_permissions_url}",
        headers=auth_header,
        json={
            "id": user_id,
            "scopes": CONFIG.security.root_user_scopes,
            "roles": CONFIG.security.root_user_roles,
        },
    )

    if not response.ok:
        raise RuntimeError(
            f"fides user permissions creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )
    else:
        logger.info(f"Created user with username: {username} and password: {password}")
