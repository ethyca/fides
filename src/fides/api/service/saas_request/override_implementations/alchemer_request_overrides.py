from typing import Any, Dict, List

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)


@register("alchemer_user_delete", [SaaSRequestType.DELETE])
def alchemer_user_delete(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    # The delete endpoint has a structure like this
    # https://api.alchemer.com/v5/contactlist/31/contactlistcontact/100012345?_method=DELETE
    # where 31 is the contact list id and 100012345 is the contact id
    # So we first get all the contact lists and extract their ids
    # Then we query for all contacts in each list, filtering on our identity email
    # Then we call a delete on the contact
    rows_deleted = 0
    params = {
        "api_token": secrets["api_key"],
        "api_token_secret": secrets["api_key_secret"],
    }
    get_list_ids = client.send(
        SaaSRequestParams(
            method=HTTPMethod.GET,
            path="/v5/contactlist",
            params=params,
        )
    )

    list_ids_data = get_list_ids.json()
    list_results = []
    for list_id in list_ids_data["data"]:
        list_results.append(list_id["id"])
    for list_result in list_results:
        contacts_data_call = client.send(
            SaaSRequestParams(
                method=HTTPMethod.GET,
                path=f"/v5/contactlist/{list_result}/contactlistcontact",
                params=params,
            )
        )
        contacts_data = contacts_data_call.json()
        for contact in contacts_data["data"]:
            for row_param_values in param_values_per_row:
                email = row_param_values["email"]
                if contact["email_address"] == email:
                    client.send(
                        SaaSRequestParams(
                            method=HTTPMethod.DELETE,
                            path=f"/v5/contactlist/{list_result}/contactlistcontact/{contact['id']}",
                            params=params,
                        )
                    )
                    rows_deleted += 1

    return rows_deleted
