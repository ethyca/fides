import logging
import uuid
from typing import Dict

import requests
import setup.constants as constants
from setup import get_secret

from fides.api.ops.api.v1 import urn_registry as urls

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_mailchimp_connector(
    auth_header: Dict[str, str],
    key: str = "mailchimp",
):
    if not key:
        key = str(uuid.uuid4())

    response = requests.get(
        f"{constants.BASE_URL}{urls.CONNECTION_BY_KEY.format(connection_key=key)}",
        headers=auth_header,
    )
    if response.status_code != 404:
        # No need to create a new connector for the given key
        return

    path = urls.SAAS_CONNECTOR_FROM_TEMPLATE.format(saas_connector_type="mailchimp")
    url = f"{constants.BASE_URL}{path}"
    response = requests.post(
        url,
        headers=auth_header,
        json={
            "instance_key": f"mailchimp_instance_{key}",
            "secrets": {
                "domain": get_secret("MAILCHIMP_DOMAIN"),
                "username": get_secret("MAILCHIMP_USERNAME"),
                "api_key": get_secret("MAILCHIMP_API_KEY"),
            },
            "name": f"Mailchimp Connector {key}",
            "description": "Mailchimp ConnectionConfig description",
            "key": key,
        },
    )

    if not response.ok:
        raise RuntimeError(
            f"fides mailchimp connector configuration failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )
