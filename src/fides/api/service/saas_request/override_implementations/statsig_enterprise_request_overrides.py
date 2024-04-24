from typing import Any, Dict, List

from fides.api.graph.execution import ExecutionNode
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.util.collection_util import Row


@register("statsig_enterprise_user_read", [SaaSRequestType.READ])
def statsig_enterprise_user_read(
    client: AuthenticatedClient,
    node: ExecutionNode,
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
