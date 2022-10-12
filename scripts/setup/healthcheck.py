from time import sleep

import requests
import setup.constants as constants

from fides.api.ops.api.v1 import urn_registry as urls


def check_health(connection_retry_count: int = 0):
    url = f"{constants.FIDES_URL}{urls.HEALTH}"
    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError:
        sleep(2)
        connection_retry_count += 1
        if connection_retry_count < 0:
            return check_health(connection_retry_count=connection_retry_count)
        else:
            raise RuntimeError(
                f"Fides health check failed! Could not connect to server at {url}."
            )

    if not response.ok:
        raise RuntimeError(
            f"Fides health check failed! response.status_code={response.status_code}, response.json()={response.json()} at url {url}"
        )
