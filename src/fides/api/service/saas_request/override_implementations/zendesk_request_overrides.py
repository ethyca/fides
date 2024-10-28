from typing import Any, Dict, List
from urllib import parse
from urllib.parse import urlsplit

import pydash

from fides.api.common_exceptions import FidesopsException
from fides.api.graph.traversal import TraversalNode
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.util.collection_util import Row

## Uplifted from Connectors-logitech
## See https://github.com/ethyca/connectors-logitech/blob/main/connectors/zendesk/zendesk_request_overrides.py#L95


def _check_tickets(tickets: List[Row], policy: Policy) -> None:
    """
    Raises an exception if there are any "open" tickets to halt the privacy request.
    Will only halt if the policy contains an erasure action.
    """
    if policy.get_rules_for_action(action_type=ActionType.erasure):
        for ticket in tickets:
            ## TODO: Check with Ramp that the Statuses list is the expected one
            if ticket["status"] in ["new", "open", "pending", "hold", "solved"]:
                raise FidesopsException("User still has open tickets, halting request")


@register("zendesk_logitech_tickets_read", [SaaSRequestType.READ])
def zendesk_logitech_tickets_read(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:

    processed_data: List[Row] = []

    for user_id in input_data.get("user_id", []):
        # initial request using user_id
        response = client.send(
            SaaSRequestParams(
                method=HTTPMethod.GET,
                path=f"/api/v2/users/{user_id}/tickets/requested.json",
                query_params={"page[size]": 100},
            )
        )

        tickets = pydash.get(response.json(), "tickets")
        _check_tickets(tickets, policy)
        processed_data.extend(tickets)

        # paginate using links.next and check each page of tickets for a chance to terminate the request early
        while pydash.get(response.json(), "links.next"):
            next_link = response.json()["links"]["next"]
            response = client.send(
                SaaSRequestParams(
                    method=HTTPMethod.GET,
                    path=urlsplit(next_link).path,
                    query_params=dict(parse.parse_qsl(urlsplit(next_link).query)),
                )
            )
            tickets = pydash.get(response.json(), "tickets")
            _check_tickets(tickets, policy)
            processed_data.extend(tickets)

    return processed_data
