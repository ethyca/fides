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


@register("appsflyer_user_read", [SaaSRequestType.READ])
def appsflyer_user_read(
    client: AuthenticatedClient,
    node: ExecutionNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    """
    Gather the full list of applications set up, and retrieve the application name and
    platform information for use with erasure endpoint.
    """

    user_ids = input_data.get("user_id", [])
    app_ids = input_data.get("app_id", [])

    users = []
    for app_id in app_ids:
        for user_id in user_ids:
            users.append({"id": user_id, "app_id": app_id})

    return users
