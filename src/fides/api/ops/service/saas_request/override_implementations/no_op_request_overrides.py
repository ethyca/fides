from typing import Any, Dict, List

from fides.api.ops.graph.traversal import TraversalNode
from fides.api.ops.models.policy import Policy
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.service.connectors.saas.authenticated_client import (
    AuthenticatedClient,
)
from fides.api.ops.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.ops.util.collection_util import Row


@register("read_no_op", [SaaSRequestType.READ])
def read_no_op(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    return [{f"{node.address.collection}_id": 1}]


@register("delete_no_op", [SaaSRequestType.DELETE])
def delete_no_op(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    return 1
