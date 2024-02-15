from typing import Any, Dict, List

import pydash

from fides.api.common_exceptions import FidesopsException
from fides.api.graph.traversal import TraversalNode
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.util.collection_util import Row
from fides.api.util.saas_util import get_identity

@register("profile_list_recipients_read", [SaaSRequestType.READ])
def profile_list_recipients_read(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    """
    Retrieve data from each profile list. 

    The members endpoint returns data in two separate arrays: one for the keys and one for the values for each result.
    {
    "recordData": {
        "fieldNames": [
        <list of field names>
        ],
        "records": [
            [
                <list of field values, corresponding to the fieldNames>
            ]
        ]
    }
    """

    list_ids = input_data.get("profile_list_id", [])
    results = []
    
    identity = get_identity(privacy_request)
    if identity == "email":
        query_ids = input_data.get("email", [])
        query_attribute = "e"
    elif identity == "phone_number":
        query_ids = input_data.get("phone_number", [])
        query_attribute = "m"
    else:
        raise FidesopsException(
            "Unsupported identity type for Oracle Responsys connector. Currently only `email` and `phone_number` are supported"
        )
    
    body = {
        "fieldList": ["all"],
        "ids": query_ids,
        "queryAttribute": query_attribute
    }

    for list_id in list_ids:
        members_response = client.send(
            SaaSRequestParams(
                method=HTTPMethod.POST,
                path=f"/rest/api/v1.3/lists/{list_id}/members",
                query_params={"action": "get"},
                body=body
            )
        )
        response_data = pydash.get(members_response.json(), 'recordData')
        serialized_data = [dict(zip(response_data["fieldNames"],records)) for records in response_data["records"]]

        results.append(serialized_data)
    return results


@register("profile_list_recipients_delete", [SaaSRequestType.DELETE])
def profile_list_recipients_delete(
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
