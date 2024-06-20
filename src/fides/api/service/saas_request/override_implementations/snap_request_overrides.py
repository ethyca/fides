import hashlib
from typing import Any, Dict, List

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


@register("snap_user_delete", [SaaSRequestType.DELETE])
def snap_user_delete(
    client: AuthenticatedClient,
    # param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> int:
    """
    The structure for Snap in this case is that at the top level there are
    Organizations
    There is an endpoint that will return the organizations as well as the ad accounts https://adsapi.snapchat.com/v1/me/organizations?with_ad_accounts=true
    This will return us all the ad account ids which we will need for subsequent calls
    We then want to call the segments endpoint to gather all segement ids
    Then we can issue the delete request against each segment with
    our processed identity email value.
    """

    rows_deleted = 0
    ad_account_ids = []
    # for GET operations against the Marketing API there is a max limit of 1000 and min of 50. I opted to set this limit to 500 as it is hard for me to imagine that there would be more than 500 'segements' or 'ad account ids' and by setting this high, it should avoid us having to deal with paging.
    params = {"limit": 500}
    # Ultimately when we call the delete endpoint we need to have a body prepared that includes the identity email, all lower case and hashed SHA256
    payload = {
        "users": [
            {
                "schema": [
                    "EMAIL_SHA256"
                ],
                "data": [
                    [
                        # need to call the signing function with our identity email following marigold example here
                        signed_email(input_data.get("email", []))
                    ]
                ]
            }
        ]
    }
    # Call to Organization endpoint
    get_organizations = client.send(
        SaaSRequestParams(
            method=HTTPMethod.GET,
            path=f"/v1/me/organizations?with_ad_accounts=true",
            headers={"Authorization": f"Bearer {secrets['access_token']}"},
            params=params,
        )
    )
    org_out = get_organizations.json()
    ad_account_ids = []
    organizations = org_out.get("organizations", [])

    # here we drill down into the return to gather up all the ad account ids
    for org_info in organizations:
        organization = org_info.get("organization", {})
        ad_accounts = organization.get("ad_accounts", [])
        for ad_account in ad_accounts:
            ad_account_ids.append(ad_account["id"])

    # here we call the segments endpoint, once for each ad account id
    for ad_account in ad_account_ids:
        get_segments = client.send(
            SaaSRequestParams(
                method=HTTPMethod.GET,
                path=f"/v1/adaccounts/{ad_account}/segments",
                headers={"Authorization": f"Bearer {secrets['access_token']}"},
                params=params,
            )
        )
        ad_out = get_segments.json()
        segments = ad_out.get("segments", [])
        # here we dive into the return to process our delete request against each segment
        for segment_info in segments:
            segment = segment_info.get("segment", {})
            segment_id = segment.get("id")
            response = client.send(
                SaaSRequestParams(
                    method=HTTPMethod.GET,
                    path=f"/v1/segments/{segment_id}/users",
                    headers={"Authorization": f"Bearer {secrets['access_token']}"},
                    params=params,
                    body=payload,
                )
            )
            assert response.ok
            rows_deleted += 1
    return rows_deleted

def signed_email(value: Any,
    input_data: Dict[str, List[Any]],
) -> Any:
    """
    What we need to do here is sha256 the email value, but there is a warning in the api docs about being sure that the email address is all lower case so we'll add that too.
    """
    prep_hash = hashlib.new('sha256')
    to_lower_email = input_data.get("email", [])
    lowered_email = to_lower_email.lower()
    hash_email = prep_hash.update(lowered_email.encode())
    processed = hash_email.hexdigest(())

    return processed
