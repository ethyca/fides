from typing import Any, Dict, List
import requests


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


@register("alchemer_user_delete", [SaaSRequestType.DELETE])
def alchemer_user_delete(
    client: AuthenticatedClient,
    node: ExecutionNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]], # may not need for our case here
    secrets: Dict[str, Any],
) -> int:
    """
    The delete endpoint has a structure like this
    https://api.alchemer.com/v5/contactlist/31/contactlistcontact/100012345?_method=DELETE
    where 31 is the contact list id
    and 100012345 is the contact id
    What we have to start with is just our identity email

    So we first get all the contact lists and extract their ids
    Then we query for all contacts in each list, filtering on our identity email
    Then we call a delete on the contact

    """
# think about paging
    # was using this as hardcoded for testing will need to pull this from input_data I think
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
            if contact['email_address'] == identity_email: # input_data.get["email"]:
                #    contact_results.append(contact)
                del_url = f"https://{secrets['domain']}/v5/contactlist/{list}/contactlistcontact/{contact['id']}"
                response = requests.request("DELETE", del_url, params=params)


    return 1
