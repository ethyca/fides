from datetime import datetime

import requests
from loguru import logger

from fides.api.ops.api.v1 import urn_registry as urls

from . import constants


def create_privacy_request(
    user_email: str,
    policy_key: str = constants.DEFAULT_ACCESS_POLICY,
):
    response = requests.post(
        f"{constants.BASE_URL}{urls.PRIVACY_REQUESTS}",
        json=[
            {
                "requested_at": str(datetime.utcnow()),
                "policy_key": policy_key,
                "identity": {"email": user_email},
            },
        ],
    )

    if not response.ok:
        raise RuntimeError(
            f"fides privacy request creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )

    created_privacy_requests = (response.json())["succeeded"]
    if len(created_privacy_requests) > 0:
        logger.info(
            f"Created fides privacy request for email={user_email} via /api/v1/privacy-request"
        )
    return response.json()["succeeded"][0]["id"]
