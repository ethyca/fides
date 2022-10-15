import logging
from typing import Dict

import requests

from fides.api.ops.api.v1 import urn_registry as urls

from . import constants

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_policy(
    auth_header: Dict[str, str],
    key: str = constants.ACCESS_POLICY_KEY,
    execution_timeframe: int = 45,
):
    policy_create_data = [
        {
            "name": key,
            "key": key,
            "execution_timeframe": execution_timeframe,
        },
    ]
    response = requests.patch(
        f"{constants.BASE_URL}{urls.POLICY_LIST}",
        headers=auth_header,
        json=policy_create_data,
    )

    if response.ok:
        policies = (response.json())["succeeded"]
        if len(policies) > 0:
            logger.info(
                "Created or updated fides policy with key=%s via /api/v1/policy", key
            )
            return

    raise RuntimeError(
        f"fides policy creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )
