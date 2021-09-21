from typing import List, Dict, Iterable

from fidesctl.core import api
from fideslang import FidesModel
from fideslang.validation import fides_key
from fideslang.parse import parse_manifest


def get_server_resources(
    url: str,
    resource_type: str,
    existing_keys: List[fides_key],
    headers: Dict[str, str],
) -> List[FidesModel]:
    """
    Get a list of resources from the server that match the provided keys.

    If the resource does not exist on the server, an error will _not_ be thrown.
    """
    raw_server_resource_list: Iterable[Dict] = filter(
        None,
        [api.get(url, resource_type, key, headers).json() for key in existing_keys],
    )
    server_resource_list: List[FidesModel] = [
        parse_manifest(resource_type, resource, from_server=True)
        for resource in raw_server_resource_list
    ]
    return server_resource_list
