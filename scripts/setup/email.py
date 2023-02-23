import logging
from typing import Dict

import requests
from setup import get_secret

from fides.api.ops.api.v1 import urn_registry as urls

from . import constants

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_email_integration(
    auth_header: Dict[str, str],
    key: str = "fides_email",
):
    response = requests.post(
        f"{constants.BASE_URL}{urls.MESSAGING_CONFIG}",
        headers=auth_header,
        json={
            "name": "fides Emails",
            "key": key,
            "service_type": "MAILGUN",
            "details": {
                "is_eu_domain": False,
                "api_version": "v3",
                "domain": get_secret("MAILGUN_SECRETS")["domain"],
            },
        },
    )

    if not response.ok:
        raise RuntimeError(
            f"fides messaging config creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )

    # Now add secrets
    email_secrets_path = urls.MESSAGING_SECRETS.format(config_key=key)
    response = requests.put(
        f"{constants.BASE_URL}{email_secrets_path}",
        headers=auth_header,
        json={
            "mailgun_api_key": get_secret("MAILGUN_SECRETS")["api_key"],
        },
    )

    if not response.ok:
        raise RuntimeError(
            f"fides messaging config secrets update failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )

    logger.info(response.json()["msg"])
