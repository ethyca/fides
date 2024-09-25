import hashlib
import json
from typing import Any, Dict, List
import math

from loguru import logger
from starlette.status import HTTP_400_BAD_REQUEST

from fides.api.graph.traversal import TraversalNode
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors.saas.authenticated_client import (
    AuthenticatedClient,
    RequestFailureResponseException,
)
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.util.collection_util import Row
from fides.api.util.logger_context_utils import request_details


@register("shipstation_order_read", [SaaSRequestType.READ])
def shipstation_order_read(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    """
    Calls shipstation `GET /orders` endpoint and processes the response to match userId"
    """

    output = []
    customer_name = input_data.get("customer_name", [None])[0]
    customer_id = input_data.get("customer_id_value", [None])[0]
    post_processed_response = {"orders": []}
    page = 1
    page_size = 50

    if not customer_name or not customer_id:
        return output

    request_params = SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/orders",
        query_params={
        "customerName": customer_name,
        "pageSize": "1",
        "page": page,
        },
    )

    response = client.send(
        request_params,
        ignore_errors=[HTTP_400_BAD_REQUEST],
    )

    response_json = response.json()
    total = response_json["total"]

    pages = math.ceil(total / page_size)

    while page <= pages:

        query_params={
            "customerName": customer_name,
            "pageSize": page_size,
            "page": page,
        }

        request_params = SaaSRequestParams(
            method=HTTPMethod.GET,
            path="/orders",
            query_params=query_params,
        )

        response = client.send(
            request_params,
            ignore_errors=[HTTP_400_BAD_REQUEST],
        )
        response_json = response.json()

        for order in response_json["orders"]:
            if order["customerId"] and order["customerId"] == customer_id:
                    post_processed_response["orders"].append(order)

        logger.bind(
            **request_details(
                client.get_authenticated_request(request_params), response
            )
        )
        if len(post_processed_response["orders"]) > 0:
            output.append(post_processed_response)

        page += 1

    return output
