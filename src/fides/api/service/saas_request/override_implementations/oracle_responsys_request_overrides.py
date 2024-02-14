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

@register("profile_lists_read", [SaaSRequestType.READ])
def profile_list_read(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    """
        Retrieve a list of profile lists to be used in downstream requests.
    """

    response = client.send(
        SaaSRequestParams(
            method=HTTPMethod.GET,
            path="/rest/api/v1.3/lists",
        )
    )

    lists = [list['name'] for list in response.json()]
    return [] if lists is None else lists

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
    Convert the statsig_user_ids from the input_data into rows. We do this because erasure
    requests only receive input data that the access request received, or data returned from
    the access request. Erasure requests can't specify data in other datasets as dependencies.
    """

    statsig_user_ids = input_data.get("user_id", [])
    results = []
    for statsig_user_id in statsig_user_ids:
        results.append({"id": statsig_user_id})
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
