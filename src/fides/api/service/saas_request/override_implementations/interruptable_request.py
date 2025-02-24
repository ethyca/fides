import os
import random
from typing import Any, Dict, List

from fides.api.graph.traversal_node import TraversalNode
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.util.collection_util import Row


@register("interruptable_request", [SaaSRequestType.READ])
def interruptable_request(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:

    # 50/50 chance to terminate the request early
    if random.random() < 0.5:
        os._exit(1)

    return []
