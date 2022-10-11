import logging
import requests
from typing import Dict

from fides.api.ops.api.v1 import urn_registry as urls

import setup.constants as constants
import secrets


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_email_integration(
    auth_header: Dict[str, str],
    key: str = "fides_email",
):
    response = requests.post(
        f"{constants.BASE_URL}{urls.EMAIL_CONFIG}",
        headers=auth_header,
        json={
            "name": "fides Emails",
            "key": key,  # TODO: Randomise this
            "service_type": "mailgun",
            "details": {
                "is_eu_domain": False,
                "api_version": "v3",
                # TODO: Where do we find this value? Can we be more specific in the docs?
                "domain": "testmail.ethyca.com",
            },
        },
    )

    if not response.ok:
        if (
            response.json()["detail"]
            != f"Only one email config is supported at a time. Config with key {key} is already configured."
        ):
            raise RuntimeError(
                f"fides email config creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
            )

    # Now add secrets
    email_secrets_path = urls.EMAIL_SECRETS.format(config_key=key)
    response = requests.put(
        f"{constants.BASE_URL}{email_secrets_path}",
        headers=auth_header,
        json={
            "mailgun_api_key": secrets.MAILGUN_API_KEY,
        },
    )

    if not response.ok:
        raise RuntimeError(
            f"fides email config secrets update failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )

    logger.info(response.json()["msg"])
