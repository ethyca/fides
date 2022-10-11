import logging
import requests

from fides.api.ops.api.v1 import urn_registry as urls

import setup.constants as constants


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def verify_subject_identity(
    privacy_request_id: str,
    code: str,
):
    verification_path = urls.PRIVACY_REQUEST_VERIFY_IDENTITY.format(
        privacy_request_id=privacy_request_id
    )
    response = requests.post(
        f"{constants.BASE_URL}{verification_path}",
        json={"code": code},
    )
    if not response.ok:
        raise RuntimeError(
            f"fides privacy request verification failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )
