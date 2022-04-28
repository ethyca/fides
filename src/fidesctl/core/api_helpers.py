"""
Reusable utilities meant to make repetitive api-related tasks easier.
"""

from typing import Dict, List, Optional

from requests import Response

from fidesctl.core import api
from fideslang import FidesModel
from fideslang.parse import parse_dict
from fideslang.validation import FidesKey


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
    server_resources: List[FidesModel] = list(
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
    return server_resources


def get_server_resource(
    url: str,
    resource_type: str,
    resource_key: str,
    headers: Dict[str, str],
) -> Optional[FidesModel]:
    """
    Attempt to get a given resource from the server.

    Returns None if the object does not exist on the server.

    As we don't always have a way to attribute fides_keys to the
    right resource, this function helps check what resource
    a fides_key belongs to by allowing us to check without errors.
    """
    raw_server_response: Response = api.get(
        url=url, resource_type=resource_type, resource_id=resource_key, headers=headers
    )

    server_resource: Optional[FidesModel] = (
        parse_dict(
            resource_type=resource_type,
            resource=raw_server_response.json(),
            from_server=True,
        )
        if raw_server_response.status_code >= 200
        and raw_server_response.status_code <= 299
        else None
    )

    return server_resource


def list_server_resources(
    url: str,
    headers: Dict[str, str],
    resource_type: str,
    exclude_keys: List[str],
) -> List[FidesModel]:
    """
    Get a list of resources from the server and return them as parsed objects.

    Returns an empty list if no resources are found or if the API returns an error.
    """
    response: Response = api.ls(url=url, resource_type=resource_type, headers=headers)
    server_resources: List[FidesModel] = (
        [
            parse_dict(
                resource_type=resource_type,
                resource=resource,
                from_server=True,
            )
            for resource in response.json()
            if isinstance(resource, dict) and resource["fides_key"] not in exclude_keys
        ]
        if response.status_code >= 200 and response.status_code <= 299
        else []
    )
    return server_resources
