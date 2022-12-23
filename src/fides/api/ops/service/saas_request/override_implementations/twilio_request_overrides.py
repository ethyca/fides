from typing import Any, Dict, List

import requests

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
from fides.api.ops.util.saas_util import to_pascal_case
from fides.core.config import get_config

CONFIG = get_config()


@register("twilio_user_update", [SaaSRequestType.UPDATE])
def twilio_user_update(
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

        auth = secrets["account_id"], secrets["password"]

        try:
            response = requests.post(
                url=f'https://{secrets["domain"]}/v1/Users/{user_id}',
                auth=auth,
                data=update_body,
            )

        # here we mimic the sort of error handling done in the core framework
        # by the AuthenticatedClient. Extenders can chose to handle errors within
        # their implementation as they wish.
        except Exception as e:
            if CONFIG.dev_mode:  # pylint: disable=R1720
                raise ConnectionException(
                    f"Operational Error connecting to Twilio Conversations API with error: {e}"
                )
            else:
                raise ConnectionException(
                    "Operational Error connecting to Twilio Conversations API."
                )
        if not response.ok:
            raise ClientUnsuccessfulException(status_code=response.status_code)

        rows_updated += 1
    return rows_updated


@register("twilio_conversation_message_update", [SaaSRequestType.UPDATE])
def twilio_conversation_message_update(
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

        auth = secrets["account_id"], secrets["password"]
        try:
            response = requests.post(
                url=f'https://{secrets["domain"]}/v1/Conversations/{conversation_id}/Messages/{message_id}',
                auth=auth,
                data=update_body,
            )

        # here we mimic the sort of error handling done in the core framework
        # by the AuthenticatedClient. Extenders can chose to handle errors within
        # their implementation as they wish.
        except Exception as e:
            if CONFIG.dev_mode:  # pylint: disable=R1720
                raise ConnectionException(
                    f"Operational Error connecting to Twilio Conversations API with error: {e}"
                )
            else:
                raise ConnectionException(
                    "Operational Error connecting to Twilio Conversations API."
                )
        if not response.ok:
            raise ClientUnsuccessfulException(status_code=response.status_code)

        rows_updated += 1
    return rows_updated
