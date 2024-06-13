from typing import Any, Dict, List

import pydash

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


@register("iterate_company_read", [SaaSRequestType.READ])
def iterate_company_read(
    client: AuthenticatedClient,
    node: ExecutionNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    """
    Retrieve a page of surveys and keep the first result
    so the company_id is accessible for downstream endpoints
    """

    response = client.send(
        SaaSRequestParams(
            method=HTTPMethod.GET,
            path="/api/v1/surveys",
        )
    )
    surveys = pydash.get(response.json(), "results")
    return [surveys[0]] if surveys else []
