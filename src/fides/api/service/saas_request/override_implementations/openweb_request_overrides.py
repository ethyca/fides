'''Notes for this particular override
For more details consult the OpenWeb documentation for their Data Protection API
The gist is that like some other vendors we do not get an email directly for this integration. This means the override is required in this case. The Endpoint speaks of this value as the <primary_key>, we are going to refer to it here as openweb_primary_key
'''

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

@register("openweb_user_read", [SaaSRequestType.READ])
def openweb_user_read(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    openweb_primary_keys = input_data.get("primary_key", [])
    results = []
    for openweb_primary_key in openweb_primary_keys:
        results.append({"primary_key": openweb_primary_key})
    return results
