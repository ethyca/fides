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
import json
import time

def signed_payload(secrets: Dict[str, Any]) -> Dict:
    """TO DO"""
    # What we need to do here is sha256 the email value, but there is a warning in the api docs about being sure that the email address is all lower case so we'll add that too.

    sub_email = secrets["identity_email"].lower()
    hash_value = hashlib.sha256(sub_email.encode())
    sig_init = hash_value.hexdigest()
    sig = str(sig_init)

    return payload


@register("snap_user_delete", [SaaSRequestType.DELETE])
def snap_user_delete(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    rows_deleted = 0
    ad_account_ids = []
    params = {"limit": 500}
    payload = json.dumps({
      "users": [
        {
          "schema": [
            "EMAIL_SHA256"
          ],
          "data": [
            [
              "c3a75685a45a565954512a7f006b691b5e06c0efe6ac28bd5c09e84bbe022b55"
            ]
          ]
        }
      ]
    })
    get_organizations = client.send(
        SaaSRequestParams(
            method=HTTPMethod.GET,
            path=f"/v1/me/organizations?with_ad_accounts=true",
            headers={"Authorization": f"Bearer {secrets['access_token']}"},
            params=params,
        )
    )

    assert get_organizations.ok
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
        assert get_segments.ok
        ad_out = get_segments.json()
        segments = ad_out.get("segments", [])
        # here we dive into the return to process our delete request against each segment
        for segment_info in segments:
            segment = segment_info.get("segment", {})
            segment_id = segment.get("id")
            response = client.send(
                SaaSRequestParams(
                    method=HTTPMethod.DELETE,
                    path=f"/v1/segments/{segment_id}/users",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {secrets['access_token']}"},
                    body=payload,
                )
            )
            time.sleep(3)
            assert response.ok
            rows_deleted += 1
    return rows_deleted
