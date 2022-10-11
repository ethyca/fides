import requests
from time import sleep

from fides.api.ops.api.v1 import urn_registry as urls

import constants


def check_health(connection_retry_count: int = 0):
    url = f"{constants.FIDESOPS_URL}{urls.HEALTH}"
    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError:
        sleep(2)
        connection_retry_count += 1
        if connection_retry_count < 4:
            return check_health(connection_retry_count=connection_retry_count)
        else:
            raise

    if not response.ok:
        raise RuntimeError(
            f"fidesops health check failed! response.status_code={response.status_code}, response.json()={response.json()} at url {url}"
        )
