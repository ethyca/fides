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




# @register("marigold_engage_user_read", [SaaSRequestType.READ])
# def marigold_engage_user_read(
#     client: AuthenticatedClient,
#     node: TraversalNode,
#     policy: Policy,
#     privacy_request: PrivacyRequest,
#     input_data: Dict[str, List[Any]],
#     secrets: Dict[str, Any],
# ) -> List[Row]:
#     """
#     Calls Marigold Engage's `GET /user` endpoint with a signed payload.
#     """

#     output = []
#     emails = input_data.get("email", [])
#     for email in emails:
#         payload = {
#             "id": email,
#             "key": "email",
#             "fields": {
#                 "activity": 1,
#                 "engagement": 1,
#                 "keys": 1,
#                 "lists": 1,
#                 "optout_email": 1,
#                 "smart_lists": 1,
#                 "vars": 1,
#                 "purchases": 1,
#                 "device": 1,
#                 "purchase_incomplete": 1,
#                 "lifetime": 1,
#             },
#         }
#         response = client.send(
#             SaaSRequestParams(
#                 method=HTTPMethod.GET,
#                 path="/user",
#                 query_params=signed_payload(secrets, payload),
#             )
#         )
#         user = response.json()
#         output.append(user)

#     return output


@register("marigold_engage_user_delete", [SaaSRequestType.DELETE])
def marigold_engage_user_delete(
    client: AuthenticatedClient,
    # param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    """
    Call to the segments endpoint to gather all segement ids
    Then we can issue the delete request against each segment with
    our processed identity email value.
    """
    all_segment_ids = []
    params = {}
    while True:
        get_segment_ids = client.send(
            SaaSRequestParams(
                method=HTTPMethod.GET,
                path=f"/adaccounts/{secrets['ad_account_id']}/segments",
                headers={"Authorization": f"Bearer {secrets['access_token_alone']}"},
                params=params,
            )
        )



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


def signed_email(value: Any,
    input_data: Dict[str, List[Any]],
) -> Any:
    """
    What we need to do here is sha256 the email value, but there is a warning in the api docs about being sure that the email address is all lower case so we'll add that too.
    """
    prep_hash = hashlib.new('sha256')
    to_lower_email = input_data.get("email", [])
    lowered_email = to_lower_email.lower()
    hash_email = prep_hash.update(lowered_email.encode())
    processed = hash_email.hexdigest(())

    return processed
