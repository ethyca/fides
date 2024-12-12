import hashlib
import json
from typing import Any, Dict, List

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)


def signed_payload(given_email: str) -> str:
    """This function is to take in the value of our identity email, and then ensure it is all lower case, and then hash it with SHA256"""
    sub_email = given_email.lower()
    hash_value = hashlib.sha256(sub_email.encode())
    sig = hash_value.hexdigest()

    return sig


@register("snap_user_delete", [SaaSRequestType.DELETE])
def snap_user_delete(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    rows_deleted = 0
    params = {"limit": 500}
    get_organizations = client.send(
        SaaSRequestParams(
            method=HTTPMethod.GET,
            path="/v1/me/organizations?with_ad_accounts=true",
            params=params,
        )
    )
    org_out = get_organizations.json()
    ad_account_ids: List[str] = []
    organizations = org_out.get("organizations", [])
    for org_info in organizations:
        organization = org_info.get("organization", {})
        ad_accounts = organization.get("ad_accounts", [])
        for ad_account in ad_accounts:
            ad_account_ids.append(ad_account["id"])
    for ad_account in ad_account_ids:
        get_segments = client.send(
            SaaSRequestParams(
                method=HTTPMethod.GET,
                path=f"/v1/adaccounts/{ad_account}/segments",
                params=params,
            )
        )
        ad_out = get_segments.json()
        segments = ad_out.get("segments", [])
        for segment_info in segments:
            segment = segment_info.get("segment", {})
            segment_id = segment.get("id")
            for row_param_values in param_values_per_row:
                email = row_param_values["email"]
                payload = json.dumps(
                    {
                        "users": [
                            {
                                "schema": ["EMAIL_SHA256"],
                                "data": [[signed_payload(email)]],
                            }
                        ]
                    }
                )
                client.send(
                    SaaSRequestParams(
                        method=HTTPMethod.DELETE,
                        path=f"/v1/segments/{segment_id}/users",
                        headers={
                            "Content-Type": "application/json",
                        },
                        body=payload,
                    )
                )
                rows_deleted += 1
    return rows_deleted
