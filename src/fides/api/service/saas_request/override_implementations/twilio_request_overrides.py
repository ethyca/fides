from typing import Any, Dict, List

from multidimensional_urlencode import urlencode as multidimensional_urlencode

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.util.saas_util import to_pascal_case


@register("twilio_user_update", [SaaSRequestType.UPDATE])
def twilio_user_update(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    rows_updated = 0

    for row_param_values in param_values_per_row:
        # get params to be used in update request
        user_id = row_param_values.get("sid")

        # check if the privacy_request targeted emails for erasure,
        # if so rewrite with a format that can be accepted by Twilio
        # regardless of the masking strategy in use
        masked_object_fields = row_param_values["masked_object_fields"]

        for k in masked_object_fields.copy().keys():
            new_key = to_pascal_case(k)
            masked_object_fields[new_key] = masked_object_fields.pop(k)

        update_body = masked_object_fields

        client.send(
            SaaSRequestParams(
                method=HTTPMethod.POST,
                path=f"/v1/Users/{user_id}",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                body=multidimensional_urlencode(update_body),
            )
        )

        rows_updated += 1
    return rows_updated


@register("twilio_conversation_message_update", [SaaSRequestType.UPDATE])
def twilio_conversation_message_update(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    rows_updated = 0

    for row_param_values in param_values_per_row:
        # get params to be used in update request
        conversation_id = row_param_values.get("conversation_id")
        message_id = row_param_values.get("message_id")

        # check if the privacy_request targeted emails for erasure,
        # if so rewrite with a format that can be accepted by Twilio
        # regardless of the masking strategy in use
        masked_object_fields = row_param_values["masked_object_fields"]

        for k in masked_object_fields.copy().keys():
            new_key = to_pascal_case(k)
            masked_object_fields[new_key] = masked_object_fields.pop(k)

        update_body = masked_object_fields

        client.send(
            SaaSRequestParams(
                method=HTTPMethod.POST,
                path=f"/v1/Conversations/{conversation_id}/Messages/{message_id}",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                body=multidimensional_urlencode(update_body),
            )
        )

        rows_updated += 1
    return rows_updated
