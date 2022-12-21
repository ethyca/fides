from json import dumps
from typing import Any, Dict, List

import pydash
from requests import get, put

from fides.api.ops.common_exceptions import (
    ClientUnsuccessfulException,
    ConnectionException,
)
from fides.api.ops.graph.traversal import TraversalNode
from fides.api.ops.models.policy import Policy
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.ops.util.collection_util import Row
from fides.core.config import get_config

CONFIG = get_config()


@register("mailchimp_messages_access", [SaaSRequestType.READ])
def mailchimp_messages_access(
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    """
    Equivalent SaaS config for the code in this function.

    Request params still need to be defined for endpoints with overrides.
    This is to provide the necessary reference and identity data as part
    of graph traversal. The resulting values are passed in as parameters
    so we don't need to define the data retrieval here.

    path: /3.0/conversations/<conversation_id>/messages
    request_params:
    - name: conversation_id
        type: path
        references:
        - dataset: mailchimp_instance
        field: conversations.id
        direction: from
    data_path: conversation_messages
    postprocessors:
    - strategy: filter
        configuration:
        field: from_email
        value:
            identity: email
    """
    # gather request params
    conversation_ids = input_data.get("conversation_id")

    # build and execute request for each input data value
    processed_data = []
    if conversation_ids:
        for conversation_id in conversation_ids:
            try:
                response = get(
                    url=f'https://{secrets["domain"]}/3.0/conversations/{conversation_id}/messages',
                    auth=(secrets["username"], secrets["api_key"]),
                )

            # here we mimic the sort of error handling done in the core framework
            # by the AuthenticatedClient. Extenders can chose to handle errors within
            # their implementation as they wish.
            except Exception as exc:  # pylint: disable=W0703
                if CONFIG.dev_mode:  # pylint: disable=R1720
                    raise ConnectionException(
                        f"Operational Error connecting to Mailchimp API with error: {exc}"
                    )
                else:
                    raise ConnectionException(
                        "Operational Error connecting to MailchimpAPI."
                    )
            if not response.ok:
                raise ClientUnsuccessfulException(status_code=response.status_code)

            # unwrap and post-process response
            response_data = pydash.get(response.json(), "conversation_messages")
            filtered_data = pydash.filter_(
                response_data,
                {"from_email": privacy_request.get_cached_identity_data().get("email")},
            )

            # build up final result
            processed_data.extend(filtered_data)

    return processed_data


@register("mailchimp_member_update", [SaaSRequestType.UPDATE])
def mailchimp_member_update(
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    rows_updated = 0
    # each update_params dict correspond to a record that needs to be updated
    for row_param_values in param_values_per_row:
        # get params to be used in update request
        list_id = row_param_values.get("list_id")
        subscriber_hash = row_param_values.get("subscriber_hash")

        # in this case, we can just put the masked object fields object
        # directly into the request body
        update_body = dumps(row_param_values["masked_object_fields"])
        try:
            response = put(
                url=f'https://{secrets["domain"]}/3.0/lists/{list_id}/members/{subscriber_hash}',
                auth=(secrets["username"], secrets["api_key"]),
                data=update_body,
            )

        # here we mimic the sort of error handling done in the core framework
        # by the AuthenticatedClient. Extenders can chose to handle errors within
        # their implementation as they wish.
        except Exception as e:
            if CONFIG.dev_mode:  # pylint: disable=R1720
                raise ConnectionException(
                    f"Operational Error connecting to mailchimp API with error: {e}"
                )
            else:
                raise ConnectionException(
                    "Operational Error connecting to mailchimp API."
                )
        if not response.ok:
            raise ClientUnsuccessfulException(status_code=response.status_code)

        rows_updated += 1
    return rows_updated
