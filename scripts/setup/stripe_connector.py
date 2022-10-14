import logging
import uuid
from typing import Dict

import requests
from setup import get_secret
import setup.constants as constants

from fides.api.ops.api.v1 import urn_registry as urls

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_stripe_connector(
    auth_header: Dict[str, str],
    key: str = "stripe",
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

    path = urls.SAAS_CONNECTOR_FROM_TEMPLATE.format(saas_connector_type="stripe")
    url = f"{constants.BASE_URL}{path}"
    response = requests.post(
        url,
        headers=auth_header,
        json={
            "name": f"Stripe Connector {key}",
            "instance_key": f"stripe_instance_{key}",
            "secrets": {
                "host": get_secret("STRIPE_HOST"),
                "api_key": get_secret("STRIPE_API_KEY"),
                "payment_types": get_secret("STRIPE_PAYMENT_TYPES"),
                "items_per_page": get_secret("STRIPE_ITEMS_PER_PAGE"),
                "identity_email": get_secret("STRIPE_IDENTITY_EMAIL"),
            },
            "description": "Stripe ConnectionConfig description",
            "key": key,
        },
    )

    if not response.ok:
        raise RuntimeError(
            f"fides Stripe connector configuration failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )
