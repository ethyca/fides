from typing import Any, Dict, List

import requests
import json

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


@register("alchemer_list_read", [SaaSRequestType.READ])
def alchemer_list_read(
    client: AuthenticatedClient,
    node: ExecutionNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]], # may not need for our case here
    secrets: Dict[str, Any],
) -> List[Row]:
    """
    Convert the statsig_user_ids from the input_data into rows. We do this because erasure
    requests only receive input data that the access request received, or data returned from
    the access request. Erasure requests can't specify data in other datasets as dependencies.

    for alchemer
    """
# think about paging
    identity_email = "connectors@ethyca.com"
    contact_list_url = f"https://{secrets['domain']}/v5/contactlist"
    params = {
        "api_token": secrets['api_token'],
        "api_token_secret": secrets['api_token_secret'],
    }
    response = requests.request("GET",contact_list_url, params=params)
    list_ids_data = response.json()

    list_results = []
    for list_id in list_ids_data['data']:
        list_results.append(list_id['id'])
    for list in list_results:
        contact_url = f"https://{secrets['domain']}/v5/contactlist/{list}/contactlistcontact"
        response = requests.request("GET", contact_url, params=params)
        contacts_data = response.json()
        # contact_results = []
        for contact in contacts_data['data']:
            if contact['email_address'] == identity_email:
            #    contact_results.append(contact)
            del_url = f"https://{secrets['domain']}/v5/contactlist/{list}/contactlistcontact/{contact['id']}"
            response = requests.request("DELETE", del_url, params=params)
