import logging
from json import dumps
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
from fides.api.ops.util.saas_util import PRIVACY_REQUEST_ID
from fides.ctl.core.config import get_config

CONFIG = get_config()
logger = logging.getLogger(__name__)


@register("twilio_user_update", [SaaSRequestType.UPDATE])
def twilio_user_update(
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    rows_updated = 0
    # each update_params dict correspond to a record that needs to be updated
    for row_param_values in param_values_per_row:
        # get params to be used in update request
        user_id = row_param_values.get("sid")

        # check if the privacy_request targeted emails for erasure,
        # if so rewrite with a format that can be accepted by Twilio
        # regardless of the masking strategy in use
        masked_object_fields = row_param_values["masked_object_fields"]

        if "user.name" in policy.get_erasure_target_categories():
            for k, v in masked_object_fields.items():
                new_key = update_to_camel_case(k)
                masked_object_fields[new_key] = masked_object_fields.pop(k)

        update_body = dumps(masked_object_fields)

        auth = secrets["account_id"], secrets["password"]
        try:
            response = requests.post(
                url=f'https://{secrets["domain"]}/v1/users/{user_id}',
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                auth=auth,
                data=update_body,
            )

        # here we mimic the sort of error handling done in the core framework
        # by the AuthenticatedClient. Extenders can chose to handle errors within
        # their implementation as they wish.
        except Exception as e:
            if CONFIG.dev_mode:  # pylint: disable=R1720
                raise ConnectionException(
                    f"Operational Error connecting to Twilio API with error: {e}"
                )
            else:
                raise ConnectionException("Operational Error connecting to Twilio API.")
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
    # each update_params dict correspond to a record that needs to be updated
    for row_param_values in param_values_per_row:
        # get params to be used in update request
        conversation_id = row_param_values.get("conversation_id")
        message_id = row_param_values.get("message_id")

        # check if the privacy_request targeted emails for erasure,
        # if so rewrite with a format that can be accepted by Twilio
        # regardless of the masking strategy in use
        masked_object_fields = row_param_values["masked_object_fields"]

        if "user.name" in policy.get_erasure_target_categories():
            for k, v in masked_object_fields.items():
                new_key = update_to_camel_case(k)
                masked_object_fields[new_key] = masked_object_fields.pop(k)

        update_body = dumps(masked_object_fields)

        auth = secrets["account_id"], secrets["password"]
        try:
            response = requests.post(
                url=f'https://{secrets["domain"]}/v1/Conversations/{conversation_id}/Messages/{message_id}',
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                auth=auth,
                data=update_body,
            )

        # here we mimic the sort of error handling done in the core framework
        # by the AuthenticatedClient. Extenders can chose to handle errors within
        # their implementation as they wish.
        except Exception as e:
            if CONFIG.dev_mode:  # pylint: disable=R1720
                raise ConnectionException(
                    f"Operational Error connecting to Twilio API with error: {e}"
                )
            else:
                raise ConnectionException("Operational Error connecting to Twilio API.")
        if not response.ok:
            raise ClientUnsuccessfulException(status_code=response.status_code)

        rows_updated += 1
    return rows_updated


def update_to_camel_case(str):
    str = str.title()
    str = str.replace("_", '')
    return str