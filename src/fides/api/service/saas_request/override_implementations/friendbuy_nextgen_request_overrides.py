from typing import Any, Dict, List

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)


@register("friendbuy_nextgen_user_delete", [SaaSRequestType.DELETE])
def friendbuy_nextgen_user_delete(
    client: AuthenticatedClient,
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

        # Since we get email like this ['<email>'], we convert it into <email> to proceed
        user_email = str(user_email)[2:-2]
        # check if the privacy_request targeted emails for erasure,
        # if so rewrite with a format that can be accepted by friendbuy_nextgen
        # regardless of the masking strategy in use

        client.send(
            SaaSRequestParams(
                method=HTTPMethod.DELETE,
                path="/v1/user-data",
                query_params={"email": user_email},
            )
        )

        rows_deleted += 1
    return rows_deleted
