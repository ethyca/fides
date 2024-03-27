from json import dumps
from typing import Any, Dict, List

import pydash

from fides.api.graph.execution import ExecutionNode
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.util.collection_util import Row


@register("mailchimp_messages_access", [SaaSRequestType.READ])
def mailchimp_messages_access(
    client: AuthenticatedClient,
    node: ExecutionNode,
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
            response = client.send(
                SaaSRequestParams(
                    method=HTTPMethod.GET,
                    path=f"/3.0/conversations/{conversation_id}/messages",
                )
            )

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
    client: AuthenticatedClient,
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

        client.send(
            SaaSRequestParams(
                method=HTTPMethod.PUT,
                path=f"/3.0/lists/{list_id}/members/{subscriber_hash}",
                body=update_body,
            )
        )

        rows_updated += 1
    return rows_updated
