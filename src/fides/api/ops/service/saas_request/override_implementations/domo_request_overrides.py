from json import dumps
from typing import Any, Dict, List

from requests import put

from fides.api.ops.common_exceptions import (
    ClientUnsuccessfulException,
    ConnectionException,
)
from fides.api.ops.models.policy import Policy
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.ops.util.saas_util import PRIVACY_REQUEST_ID
from fides.core.config import get_config

CONFIG = get_config()


@register("domo_user_update", [SaaSRequestType.UPDATE])
def domo_user_update(
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    rows_updated = 0
    # each update_params dict correspond to a record that needs to be updated
    for row_param_values in param_values_per_row:
        # get params to be used in update request
        user_id = row_param_values.get("user_id")

        # check if the privacy_request targeted emails for erasure,
        # if so rewrite with a format that can be accepted by Domo
        # regardless of the masking strategy in use
        all_object_fields = row_param_values["all_object_fields"]

        if "user.contact.email" in policy.get_erasure_target_categories():
            privacy_request_id = row_param_values[PRIVACY_REQUEST_ID]
            all_object_fields["email"] = f"{privacy_request_id}@company.com"
            all_object_fields["alternateEmail"] = f"{privacy_request_id}@company.com"

        update_body = dumps(all_object_fields)

        try:
            response = put(
                url=f'https://{secrets["domain"]}/v1/users/{user_id}',
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {secrets['access_token']}",
                },
                data=update_body,
            )

        # here we mimic the sort of error handling done in the core framework
        # by the AuthenticatedClient. Extenders can chose to handle errors within
        # their implementation as they wish.
        except Exception as e:
            if CONFIG.dev_mode:  # pylint: disable=R1720
                raise ConnectionException(
                    f"Operational Error connecting to Domo API with error: {e}"
                )
            else:
                raise ConnectionException("Operational Error connecting to Domo API.")
        if not response.ok:
            raise ClientUnsuccessfulException(status_code=response.status_code)

        rows_updated += 1
    return rows_updated
