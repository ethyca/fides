from json import dumps
from typing import Any, Dict, List

from loguru import logger

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.util.saas_util import PRIVACY_REQUEST_ID


@register("salesforce_contact_update", [SaaSRequestType.UPDATE])
def salesforce_contact_update(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    rows_updated = 0
    # each update_params dict correspond to a record that needs to be updated
    for row_param_values in param_values_per_row:
        # check if the masked field is over 40 characters long
        # if so, truncate it
        masked_object_fields = row_param_values["masked_object_fields"]
        for key in masked_object_fields:
            logger.info("key: %s", key)
            logger.info("size: %s", len(masked_object_fields[key]))
            if(len(masked_object_fields[key])>40):
                masked_object_fields[key] = masked_object_fields[key][:40]

        update_body = dumps(masked_object_fields)
        contact_id = row_param_values["contact_id"]
        client.send(
            SaaSRequestParams(
                method=HTTPMethod.PATCH,
                headers={"Content-Type": "application/json"},
                path=f"/services/data/v54.0/sobjects/Contact/{contact_id}",
                body=update_body,
            )
        )
        rows_updated += 1
    return rows_updated
