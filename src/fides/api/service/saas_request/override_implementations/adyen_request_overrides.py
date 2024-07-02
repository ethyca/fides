"""Notes for this particular override
For more details consult the Adyen documentation for their Data Protection API
The gist is that like some other vendors we do not get an email directly for this integration. The data protection endpoint in this case has two main requirements, called merchantAccount and pspReference.
"""

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


@register("adyen_user_read", [SaaSRequestType.READ])
def adyen_user_read(
    client: AuthenticatedClient,
    node: ExecutionNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    adyen_user_ids = input_data.get("user_id", [])
    results = []
    for adyen_user_id in adyen_user_ids:
        results.append({"psp_reference": adyen_user_id})
    return results
