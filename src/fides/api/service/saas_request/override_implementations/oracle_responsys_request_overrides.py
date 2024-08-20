import json
from typing import Any, Dict, List

import pydash
from requests import Response

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


def oracle_responsys_config_parse_profile_lists(list_restrictions: str) -> List[str]:
    """
    Parses the list of profile lists entered as part of the connector params from comma-delimited values. Special value "all" indicates that all profile lists are in-scope.
    """
    profile_lists = []

    if list_restrictions != "all":
        profile_lists = list_restrictions.split(",")

    return profile_lists


def oracle_responsys_config_parse_profile_extensions(
    extension_restrictions: str,
) -> Dict[str, List[str]]:
    """
    Parses the list of profile extensions entered as part of the connector params from comma-delimited values. Profile extensions are expected to be in the format of `<profile_list>.<profile_extension>`. Special value "all" indicates that all profile extensions are in-scope.
    """
    unparsed_profile_extensions = []
    profile_extensions: Dict[str, List[str]] = {}

    if extension_restrictions != "all":
        unparsed_profile_extensions = extension_restrictions.split(",")
        for extension in unparsed_profile_extensions:
            ext = extension.split(".")
            if len(ext) > 2:
                raise FidesopsException(
                    "Profile extension could not be parsed, more than one '.' found."
                )
            if len(ext) < 2:
                raise FidesopsException(
                    "Profile extension could not be parsed, '.' not found."
                )
            if ext[0] in profile_extensions:
                profile_extensions[ext[0]].append(ext[1])
            else:
                profile_extensions[ext[0]] = [ext[1]]

    return profile_extensions


def oracle_responsys_serialize_record_data(response: Response) -> List[Dict[Any, Any]]:
    """
    Serializes response data from two separate arrays: one for the keys and one for the values for each result, returning a list of dicts.
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
    response_data = pydash.get(response.json(), "recordData")
    serialized_data = []
    if response_data:
        normalized_field_names = [
            field.lower().rstrip("_") for field in response_data["fieldNames"]
        ]
        serialized_data = [
            dict(zip(normalized_field_names, records))
            for records in response_data["records"]
        ]
    return serialized_data


def oracle_responsys_get_profile_extensions(
    client: AuthenticatedClient, list_ids: List[str]
) -> Dict[str, List[str]]:
    """
    Retrieves a list of profile_extensions for each profile_list, returned as a dict.
    """
    results = {}

    for list_id in list_ids:
        list_extensions_response = client.send(
            SaaSRequestParams(
                method=HTTPMethod.GET,
                path=f"/rest/api/v1.3/lists/{list_id}/listExtensions",
            )
        )
        profile_extension_names = pydash.map_(
            list_extensions_response.json(), "profileExtension.objectName"
        )
        results[list_id] = profile_extension_names
    return results


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
    """
    results = []

    list_ids_from_api = input_data.get("profile_list_id", [])
    list_ids_from_config_str = secrets["profile_lists"]

    if list_ids_from_config_str != "all":
        list_ids_from_config = list_ids_from_config_str.split(",")
        # Because Fides will ignore 404s, make sure lists exist, so 404s will only come from the recipient not being found.
        for list_id in list_ids_from_config:
            if list_id not in list_ids_from_api:
                raise FidesopsException("Profile list not found.")
        list_ids = list_ids_from_config
    else:
        list_ids = list_ids_from_api

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
        serialized_data = oracle_responsys_serialize_record_data(members_response)
        if serialized_data:
            for record in serialized_data:
                # Filter out the keys with falsy values and append it
                filtered_records = {
                    key: value for key, value in record.items() if value
                }
                filtered_records["profile_list_id"] = list_id
                results.append(filtered_records)
    return results


@register("oracle_responsys_profile_extension_recipients_read", [SaaSRequestType.READ])
def oracle_responsys_profile_extension_recipients_read(
    client: AuthenticatedClient,
    node: ExecutionNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    """
    Retrieve a list of profile extension tables and returns the data from each profile extension table for the RIIDs.
    """
    list_ids = input_data.get("profile_list_id", [])
    riids = input_data.get("responsys_id", [])

    results = []
    extensions: Dict[str, List[str]] = {}

    # If config sets the list of extensions, then use it. Otherwise, all extensions are in scope.
    extensions_from_config = oracle_responsys_config_parse_profile_extensions(
        secrets["profile_extensions"]
    )
    extensions_from_api = oracle_responsys_get_profile_extensions(client, list_ids)
    if extensions_from_config:
        # Because Fides will ignore 404s, make sure lists/extensions exist, so 404s will only come from the recipient not being found.
        for key, value in extensions_from_config.items():
            if key not in list_ids:
                raise FidesopsException(
                    "Profile extension does not belong to a valid profile list."
                )
            for profile_extension in value:
                if profile_extension not in extensions_from_api[key]:
                    raise FidesopsException("Profile extension not found.")
        extensions = extensions_from_config
    else:
        extensions = extensions_from_api

    body = {
        "fieldList": ["all"],
        "ids": riids,
        "queryAttribute": "r",
    }  # queryAttribute 'r' represents RIID

    for key, value in extensions.items():
        for profile_extension in value:
            list_extensions_response = client.send(
                SaaSRequestParams(
                    method=HTTPMethod.POST,
                    path=f"/rest/api/v1.3/lists/{key}/listExtensions/{profile_extension}/members",
                    query_params={"action": "get"},
                    body=json.dumps(body),
                    headers={"Content-Type": "application/json"},
                ),
                [404],
            )

            serialized_data = oracle_responsys_serialize_record_data(
                list_extensions_response
            )

            for record in serialized_data:
                results.append(
                    {
                        "profile_extension_id": profile_extension,
                        "riid": record.pop("riid", None),
                        # PETs schemas are fully dynamic, o we need to treat the record as a JSON string in order to treat it as user data.
                        "user_data": json.dumps(record),
                    }
                )
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
                ),
                [404],
            )

            rows_deleted += 1
    return rows_deleted
