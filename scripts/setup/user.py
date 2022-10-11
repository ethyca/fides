import logging
import requests
import uuid
from typing import Dict

from fides.api.ops.api.v1.scope_registry import SCOPE_REGISTRY
from fides.api.ops.api.v1 import urn_registry as urls

import setup.constants as constants

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_user(
    auth_header: Dict[str, str],
    username: str = None,
    password: str = "Atestpassword1!",
):
    """Adds a user with full permissions"""
    if not username:
        username = str(uuid.uuid4())

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
            "scopes": SCOPE_REGISTRY,
        },
    )

    if not response.ok:
        raise RuntimeError(
            f"fides user permissions creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )
    else:
        logger.info(f"Created user with username: {username} and password: {password}")
