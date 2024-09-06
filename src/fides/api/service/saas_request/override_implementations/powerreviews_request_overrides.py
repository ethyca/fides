import json
from typing import Any, Dict, List

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)


@register("powerreviews_user_delete", [SaaSRequestType.DELETE])
def powerreviews_user_delete(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    """
    Calls PowerReviews's `POST right-to-be-forgotten` endpoint with the correct base URL, and with the email in JSON format
    """

    rows_deleted = 0

    client.uri = "https://privacy-api.powerreviews.com"
    path = "/v1/privacy/right-to-be-forgotten?delete_ugc=true&opt_out_email=true"

    headers = {
        "Content-Type": "application/json",
    }

    for row_param_values in param_values_per_row:
        email = row_param_values["email"]

        payload = json.dumps({"requests": [{"email": email}]})

        client.send(
            SaaSRequestParams(
                method=HTTPMethod.POST,
                path=path,
                headers=headers,
                body=payload,
            )
        )

        rows_deleted += 1

    return rows_deleted
