from json import dumps
from typing import Any, Dict, List

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.util.saas_util import PRIVACY_REQUEST_ID


@register("hubspot_contacts_update", [SaaSRequestType.UPDATE])
def hubspot_contacts_update(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    rows_updated = 0
    # each update_params dict correspond to a record that needs to be updated
    for row_param_values in param_values_per_row:
        # check if the privacy_request targeted emails for erasure,
        # if so rewrite with a format that can be accepted by hubspot
        # regardless of the masking strategy in use
        masked_object_fields = row_param_values["masked_object_fields"]

        if "email" in masked_object_fields["properties"]:
            privacy_request_id = row_param_values[PRIVACY_REQUEST_ID]
            masked_object_fields["properties"][
                "email"
            ] = f"{privacy_request_id}@company.com"

        update_body = dumps(masked_object_fields)
        contact_id = row_param_values["contactId"]
        client.send(
            SaaSRequestParams(
                method=HTTPMethod.PATCH,
                headers={"Content-Type": "application/json"},
                path=f"/crm/v3/objects/contacts/{contact_id}",
                body=update_body,
            )
        )
        rows_updated += 1
    return rows_updated
