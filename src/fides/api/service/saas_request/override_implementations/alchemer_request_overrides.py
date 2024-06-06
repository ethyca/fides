from typing import Any, Dict, List

import pydash
import json

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


@register("alchemer_list_read", [SaaSRequestType.READ])
def alchemer_list_read(
    client: AuthenticatedClient,
    node: ExecutionNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]], # may not need for our case here
    secrets: Dict[str, Any],
) -> List[Row]:
    """
    Convert the statsig_user_ids from the input_data into rows. We do this because erasure
    requests only receive input data that the access request received, or data returned from
    the access request. Erasure requests can't specify data in other datasets as dependencies.

    for alchemer
    """
# think about paging

    params = {
        "api_token": secrets['api_token'],
        "api_token_secret": secrets['api_token_secret'],
    }
    response = client.send(
        SaaSRequestParams(
            method=HTTPMethod.GET,
            path="/v5/contactlist",
            query_params=params,
        )
    )

    list_ids_data = pydash.get(response.json())
    list_ids = json.loads(list_ids_data)
    ids = [item['id'] for item in list_ids['data']]
    results = []
    for list_id in list_ids:
        results.append({"id": list_id})
    return results

    # statsig_user_ids = input_data.get("user_id", [])
    # results = []
    # for statsig_user_id in statsig_user_ids:
    #     results.append({"id": statsig_user_id})
    # return results
