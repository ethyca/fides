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

### NOTE this has been stolen from stasig ###


@register("adyen_user_read", [SaaSRequestType.READ])
def adyen_user_read(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    ### Note - the value we are actually getting is a string that represents a PSP reference of the original payment authorisation. This is what Adyen uses to remove all data about a particular shopper
    adyen_users_id = input_data.get("user_id", [])
    results = []
    for adyen_user_id in adyen_users_id:
        results.append({"pspReference": adyen_user_id})
    return results
