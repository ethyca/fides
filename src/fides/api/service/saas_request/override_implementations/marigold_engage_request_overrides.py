import hashlib
import json
from typing import Any, Dict, List

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


@register("marigold_engage_test", [SaaSRequestType.TEST])
def marigold_engage_test(client: AuthenticatedClient, secrets: Dict[str, Any]) -> None:
    """
    Calls Marigold Engage's `GET /list` endpoint with a signed payload.
    """

    client.send(
        SaaSRequestParams(
            method=HTTPMethod.GET,
            path="/list",
            query_params=signed_payload(secrets, {}),
        )
    )


@register("marigold_engage_user_read", [SaaSRequestType.READ])
def marigold_engage_user_read(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    """
    Calls Marigold Engage's `GET /user` endpoint with a signed payload.
    """

    output = []
    emails = input_data.get("email", [])
    for email in emails:
        payload = {
            "id": email,
            "key": "email",
            "fields": {
                "activity": 1,
                "engagement": 1,
                "keys": 1,
                "lists": 1,
                "optout_email": 1,
                "smart_lists": 1,
                "vars": 1,
                "purchases": 1,
                "device": 1,
                "purchase_incomplete": 1,
                "lifetime": 1,
            },
        }
        response = client.send(
            SaaSRequestParams(
                method=HTTPMethod.GET,
                path="/user",
                query_params=signed_payload(secrets, payload),
            )
        )
        user = response.json()
        output.append(user)

    return output


@register("marigold_engage_user_delete", [SaaSRequestType.DELETE])
def marigold_engage_user_delete(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    """
    Calls Marigold Engage's `DELETE /user` endpoint with a signed payload.
    """

    rows_deleted = 0
    for row_param_values in param_values_per_row:
        email = row_param_values["email"]
        client.send(
            SaaSRequestParams(
                method=HTTPMethod.DELETE,
                path="/user",
                query_params=signed_payload(secrets, {"id": email}),
            )
        )
        rows_deleted += 1
    return rows_deleted


def signed_payload(secrets: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a signed payload dictionary with an MD5 hash of the secret, API key, format, and payload.
    """

    # the signature is the md5 hash of the concatenated string
    # of secret, API key, format, and stringified payload
    stringified_payload = json.dumps(payload)
    parameter_values = (
        f'{secrets["secret"]}{secrets["api_key"]}json{stringified_payload}'
    )
    hash_value = hashlib.md5(parameter_values.encode())
    sig = hash_value.hexdigest()

    return {
        "api_key": secrets["api_key"],
        "sig": sig,
        "format": "json",
        "json": stringified_payload,
    }
