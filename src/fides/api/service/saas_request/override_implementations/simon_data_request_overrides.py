import json
import time
from typing import Any, Dict, List

import pydash

from fides.api.graph.traversal import TraversalNode
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.util.collection_util import Row

ACCESS_REQUEST_TIMEOUT_SECONDS: int = 60 * 5  # 5 minutes from now


@register("simon_data_access", [SaaSRequestType.READ])
def simon_data_access(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    """
    #TODO
    Equivalent SaaS config for the code in this function.

    Request params still need to be defined for endpoints with overrides.
    This is to provide the necessary reference and identity data as part
    of graph traversal. The resulting values are passed in as parameters
    so we don't need to define the data retrieval here.

    Simon Data processes the data access request asynchronously, and we
    need to poll the API for completion. This override polls the API for 5 minutes
    by default, pausing for 10 seconds between each check.
    """
    # gather request params
    email = input_data.get("user_email")

    # execute the initial access request

    payload = json.dumps({"email_address": email})

    request_response = client.send(
        SaaSRequestParams(
            method=HTTPMethod.POST,
            path="/v1/privacy/export/",
            body=payload,
        )
    )

    # retrieve the access request id to poll with
    access_request_id = pydash.get(request_response.json(), "id")

    # build and execute request for each input data value

    if access_request_id:
        timeout = time.time() + ACCESS_REQUEST_TIMEOUT_SECONDS
        while time.time() > timeout:
            access_request_status_response = client.send(
                SaaSRequestParams(
                    method=HTTPMethod.GET,
                    path=f"/v1/privacy/export/{access_request_id}",
                )
            )
            get_response_state = pydash.get(
                access_request_status_response.json(), "state"
            )
            if get_response_state == "Completed":
                get_response_data = access_request_status_response.json()
                export_url = get_response_data["export_url"]
                export_response = client.send(
                    SaaSRequestParams(
                        method=HTTPMethod.GET,
                        path=export_url,
                    )
                )
                break
            time.sleep(10)
    # TODO create a better response for timeout exceeded waiting for access request
    return export_response
