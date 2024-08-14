from typing import Any, Dict, List

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)


@register("microsoft_advertising_user_delete", [SaaSRequestType.DELETE])
def microsoft_advertising_user_delete(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    rows_updated = 0

    for row_param_values in param_values_per_row:
        # API calls go here, look at other request overrides in this directory as examples
        rows_updated += 1

    return rows_updated
