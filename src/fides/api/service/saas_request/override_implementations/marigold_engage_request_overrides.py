import hashlib
import json
import urllib
import urllib.parse
from typing import Any, Dict, List
from urllib.parse import quote

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


@register("marigold_engage_user_read", [SaaSRequestType.READ])
def marigold_engage_user_read(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    """
    TBD
    """
    output = []
    emails = input_data.get("email", [])
    for email in emails:
        payload = {
            "id": email,
            "key": "email",
            "fields": {
                "activity": 1,
                "engagement": 1,
                "keys": 1,
                "lists": 1,
                "optout_email": 1,
                "smart_lists": 1,
                "vars": 1,
                "purchases": 1,
                "device": 1,
                "purchase_incomplete": 1,
                "lifetime": 1,
            },
        }
        stringified_payload = json.dumps(payload, separators=(",", ":"))
        # import pdb

        # pdb.set_trace()
        sig = payload_signature(secrets, stringified_payload)

        response = client.send(
            SaaSRequestParams(
                method=HTTPMethod.GET,
                path="/user",
                query_params={
                    "api_key": secrets["api_key"],
                    "sig": sig,
                    "format": "json",
                    "json": stringified_payload,
                },
            )
        )
        user = response.json()
        output.append(user)

    return output

# @register("marigold_engage_user_delete", [SaaSRequestType.DELETE])
# def marigold_engage_user_delete(
#     client: AuthenticatedClient,
#     node: TraversalNode,
#     policy: Policy,
#     privacy_request: PrivacyRequest,
#     input_data: Dict[str, List[Any]],
#     secrets: Dict[str, Any],
#     marigold_engage_secrets,
#     marigold_engage_erasure_identity_email,
# ) -> List[Row]:
#     base_url = f'https://api.sailthru.com/user'
#     email_test = marigold_engage_erasure_identity_email
#     email_prep = '{"id":"'+email_test+'"}'
#     headers = {
#         'Content-Type': 'application/x-www-form-urlencoded'
#         }   
#     ''' Setup to deal with the signature (sig) requirement
#     Here we need to generate an MD5 hash based on the secret, api_key, format and the email of the user, converted into a string to compose the email into the format required.
#     '''
#     output = []
#     sig_prep = marigold_engage_secrets["secret"]+marigold_engage_secrets["api_key"]+"json"+email_prep
#     sig_chk = md5_any(sig_prep)
#     md5_readable = sig_chk.hexdigest()
#     ### end sig prep    
#     response = client.send(
#         SaaSRequestParams(
#             method=HTTPMethod.DELETE,
#             path="/user",
#             query_params={
#                 "api_key": secrets["api_key"],
#                 "sig": md5_readable,
#                 "format": "json",
#                 "json": email_prep,
#             },
#         )
#     )
#     import pdb

#     pdb.set_trace()
    
#     assert response.ok
#     user = response.json()
#     output.append(user)

#     return output    




def payload_signature(secrets: Dict[str, Any], payload: str):
    values = [secrets["secret"], secrets["api_key"], "json", payload]
    return md5_any("".join(values)).hexdigest()


def md5_any(value_to_MD5) -> str:
    return hashlib.md5(value_to_MD5.encode())


def url_encode(value_to_encode) -> str:
    return urllib.parse.quote_plus(value_to_encode)
