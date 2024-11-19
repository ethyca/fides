import hashlib
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


@register("segment_delete_md5", [SaaSRequestType.DELETE])
def segment_delete_md5(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    rows_deleted = 0

    headers = {
        "Content-Type": "application/json",
    }

    for row_param_values in param_values_per_row:
        email = row_param_values["email"]
        hashed_email = hashlib.md5(email.encode("utf-8")).hexdigest()

        payload = json.dumps(
            {
                "regulation_type": "Suppress_With_Delete",
                "attributes": {"name": "userId", "values": [hashed_email]},
            }
        )

        workspace_name = row_param_values["workspace_name"]

        client.send(
            SaaSRequestParams(
                method=HTTPMethod.POST,
                path=f"/v1beta/workspaces/{workspace_name}/regulations",
                headers=headers,
                body=payload,
            )
        )
        rows_deleted += 1

    return rows_deleted
