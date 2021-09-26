"""
Reusable utilities meant to make repetitive api-related tasks easier.
"""

from typing import List, Dict, Iterable

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
    raw_server_resource_list: Iterable[Dict] = filter(
        None,
        [api.get(url, resource_type, key, headers).json() for key in existing_keys],
    )
    server_resource_list: List[FidesModel] = [
        parse_dict(resource_type, resource, from_server=True)
        for resource in raw_server_resource_list
    ]
    return server_resource_list
