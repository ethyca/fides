import logging
import requests
from typing import Optional

from fides.api.ops.api.v1.scope_registry import SCOPE_REGISTRY
from fides.api.ops.api.v1 import urn_registry as urls

import constants


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def get_access_token(
    client_id: str,
    client_secret: str,
) -> str:
    """
    Authorize with fidesops via OAuth.
    Returns a valid access token if successful, or throws an error otherwise.
    """
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    url = f"{constants.BASE_URL}{urls.TOKEN}"
    response = requests.post(url, data=data)

    if response.ok:
        token = (response.json())["access_token"]
        if token:
            logger.info(f"Completed fidesops oauth login via {url}")
            return token

    raise RuntimeError(
        f"fidesops oauth login failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def create_oauth_client(auth_token: str):
    """
    Create a new OAuth client in fidesops.
    Returns the response JSON if successful, or throws an error otherwise.
    """
    oauth_header = {"Authorization": f"Bearer {auth_token}"}
    response = requests.post(
        f"{constants.BASE_URL}{urls.CLIENT}",
        headers=oauth_header,
        json=SCOPE_REGISTRY,
    )

    if response.ok:
        created_client = response.json()
        if created_client["client_id"] and created_client["client_secret"]:
            logger.info("Created fidesops oauth client via /api/v1/oauth/client")
            return created_client["client_id"], created_client["client_secret"]

    raise RuntimeError(
        f"fidesops oauth client creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def get_auth_header(
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
):
    """Use the root oauth client to create a new client"""
    if not client_id or not client_secret:
        root_token = get_access_token(
            client_id=constants.ROOT_CLIENT_ID,
            client_secret=constants.ROOT_CLIENT_SECRET,
        )
        client_id, client_secret = create_oauth_client(auth_token=root_token)

    auth_token = get_access_token(client_id, client_secret)
    return {"Authorization": f"Bearer {auth_token}"}
