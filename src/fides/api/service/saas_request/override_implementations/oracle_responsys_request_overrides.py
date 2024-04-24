import json
from typing import Any, Dict, List

import pydash

from fides.api.common_exceptions import FidesopsException
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
from fides.api.util.saas_util import get_identity


@register("oracle_responsys_profile_list_recipients_read", [SaaSRequestType.READ])
def oracle_responsys_profile_list_recipients_read(
    client: AuthenticatedClient,
    node: ExecutionNode,
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
        # Oracle Responsys doesn't support the initial + in phone numbers
        for idx, query_id in enumerate(query_ids):
            query_ids[idx] = query_id[1:] if query_id.startswith("+") else query_id
        query_attribute = "m"
    else:
        raise FidesopsException(
            "Unsupported identity type for Oracle Responsys connector. Currently only `email` and `phone_number` are supported"
        )

    body = {"fieldList": ["all"], "ids": query_ids, "queryAttribute": query_attribute}
    for list_id in list_ids:
        members_response = client.send(
            SaaSRequestParams(
                method=HTTPMethod.POST,
                path=f"/rest/api/v1.3/lists/{list_id}/members",
                query_params={"action": "get"},
                body=json.dumps(body),
                headers={"Content-Type": "application/json"},
            ),
            [404],  # Returns a 404 if no list member is found
        )
        response_data = pydash.get(members_response.json(), "recordData")
        if response_data:
            normalized_field_names = [
                field.lower().rstrip("_") for field in response_data["fieldNames"]
            ]
            serialized_data = [
                dict(zip(normalized_field_names, records))
                for records in response_data["records"]
            ]

            for record in serialized_data:
                # Filter out the keys with falsy values and append it
                filtered_records = {
                    key: value for key, value in record.items() if value
                }
                filtered_records["profile_list_id"] = list_id
                results.append(filtered_records)

    return results


@register("oracle_responsys_profile_list_recipients_delete", [SaaSRequestType.DELETE])
def oracle_responsys_profile_list_recipients_delete(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    """
    Deletes data from each profile list. Upon deletion from the list, PET data is also deleted.
    """
    rows_deleted = 0
    # each delete_params dict correspond to a record that needs to be deleted
    for row_param_values in param_values_per_row:
        # get params to be used in delete request
        all_object_fields = row_param_values["all_object_fields"]

        list_id = all_object_fields["profile_list_id"]
        responsys_id = row_param_values.get("responsys_id")

        if responsys_id:
            client.send(
                SaaSRequestParams(
                    method=HTTPMethod.DELETE,
                    path=f"/rest/api/v1.3/lists/{list_id}/members/{responsys_id}",
                )
            )

            rows_deleted += 1
    return rows_deleted
