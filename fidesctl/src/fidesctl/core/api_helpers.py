"""
Reusable utilities meant to make repetitive api-related tasks easier.
"""

from typing import List, Dict, Optional

from fidesctl.core import api
from fideslang import FidesModel
from fideslang.validation import FidesKey
from fideslang.parse import parse_dict


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
    Get a given resource from the server

    Returns None if the object does not exist on the server
    """
    raw_server_response: Dict = api.get(
        url=url, resource_type=resource_type, resource_id=resource_key, headers=headers
    ).json()

    server_resource: Optional[FidesModel] = (
        parse_dict(
            resource_type=resource_type, resource=raw_server_response, from_server=True
        )
        if raw_server_response
        else None
    )
    return server_resource
