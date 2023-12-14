from typing import Any, Dict, List

from fides.api.graph.traversal import TraversalNode
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.util.collection_util import Row


@register("appsflyer_get_app_names", [SaaSRequestType.READ])
def appsflyer_get_app_names(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    """
    Gather the full list of applications set up, and retrieve the application name and
    platform information for use with erasure endpoint.
    """

    appsflyer_app_ids = input_data.get("user_id", [])
    results = []
    for statsig_user_id in statsig_user_ids:
        results.append({"id": statsig_user_id})
    return results
