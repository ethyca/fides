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

    response = client.send(
        SaaSRequestParams(
            method=HTTPMethod.GET,
            path="/api/mng/apps",
        )
    )
    ## Getting a single value doesn't look too hard, but how to get more than one?
    app_names = pydash.get(response.json(), "data")
    ## need to loop to process all the app names (ids) we're about to go through
    ## we need to submit a erasure request once with each app name to ensure we get
    ## all the correct names for use.
    ## can we do a for each based on the number of app names we get back and issue an
    ## erasure request for each app name with all other params the same?
    return [id[0]] if app_names else []
