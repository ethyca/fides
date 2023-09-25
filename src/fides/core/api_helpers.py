"""
Reusable utilities meant to make repetitive api-related tasks easier.
"""

from typing import Dict, List, Optional

from fideslang.models import FidesModel
from fideslang.parse import parse_dict
from fideslang.validation import FidesKey
from requests import Response

from fides.common.utils import check_response_auth
from fides.core import api


def get_server_resources(
    url: str,
    resource_type: str,
    existing_keys: List[FidesKey],
    headers: Dict[str, str],
) -> List[FidesModel]:
    """
    Get a list of resources from the server that match the provided keys.

    If the resource does not exist on the server, an error will _not_ be thrown.
    Instead, an empty object will be stored and then filtered out.
    """
    raw_server_resources = list(
        filter(
            None,
            [
                get_server_resource(
                    url=url,
                    resource_type=resource_type,
                    resource_key=key,
                    headers=headers,
                )
                for key in existing_keys
            ],
        )
    )
    server_resources: List[FidesModel] = [
        parse_dict(resource_type=resource_type, resource=resource, from_server=True)
        for resource in raw_server_resources
    ]

    return server_resources


def get_server_resource(
    url: str,
    resource_type: str,
    resource_key: str,
    headers: Dict[str, str],
) -> Dict:
    """
    Attempt to get a given resource from the server.

    Returns {} if the object does not exist on the server.

    As we don't always have a way to attribute fides_keys to the
    right resource, this function helps check what resource
    a fides_key belongs to by allowing us to check without errors.
    """
    raw_server_response: Response = check_response_auth(
        api.get(
            url=url,
            resource_type=resource_type,
            resource_id=resource_key,
            headers=headers,
        )
    )

    raw_server_resource: Optional[Dict] = (
        raw_server_response.json()
        if raw_server_response.status_code >= 200
        and raw_server_response.status_code <= 299
        else None
    )

    return raw_server_resource or {}


def list_server_resources(
    url: str,
    headers: Dict[str, str],
    resource_type: str,
    exclude_keys: List[str],
) -> Optional[List[Dict]]:
    """
    Get a list of resources from the server and return them as parsed objects.

    Returns an empty list if no resources are found or if the API returns an error.
    """
    response: Response = check_response_auth(
        api.ls(url=url, resource_type=resource_type, headers=headers)
    )
    raw_server_resources: Optional[List[Dict]] = (
        [
            resource
            for resource in response.json()
            if isinstance(resource, dict) and resource["fides_key"] not in exclude_keys
        ]
        if response.status_code >= 200 and response.status_code <= 299
        else []
    )

    return raw_server_resources
