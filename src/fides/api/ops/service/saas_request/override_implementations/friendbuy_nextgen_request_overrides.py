import logging
from typing import Any, Dict, List

from requests import delete

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
from fides.ctl.core.config import get_config

CONFIG = get_config()
logger = logging.getLogger(__name__)


@register("friendbuy_nextgen_user_delete", [SaaSRequestType.DELETE])
def friendbuy_nextgen_user_delete(
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    rows_deleted = 0
    # each delete_params dict correspond to a record that needs to be deleted
    for row_param_values in param_values_per_row:
        # get params to be used in delete request
        user_email = row_param_values.get("email")

        # Since we get email ilike this ['<email>'], we convert it into <email> to proceed
        user_email = str(user_email)[2:-2]
        # check if the privacy_request targeted emails for erasure,
        # if so rewrite with a format that can be accepted by friendbuy_nextgen
        # regardless of the masking strategy in use

        try:
            response = delete(
                url=f'https://{secrets["domain"]}/v1/user-data?email={user_email}',
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {secrets['token']}",
                },
            )

        # here we mimic the sort of error handling done in the core framework
        # by the AuthenticatedClient. Extenders can chose to handle errors within
        # their implementation as they wish.
        except Exception as e:
            if CONFIG.dev_mode:  # pylint: disable=R1720
                raise ConnectionException(
                    f"Operational Error connecting to friendbuy_nextgen API with error: {e}"
                )
            else:
                raise ConnectionException(
                    "Operational Error connecting to friendbuy_nextgen API."
                )
        if not response.ok:
            raise ClientUnsuccessfulException(status_code=response.status_code)

        rows_deleted += 1
    return rows_deleted
