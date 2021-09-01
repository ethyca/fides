from typing import List, Dict, Iterable

from fidesctl.core import api
from fideslang import FidesModel
from fideslang.models.validation import FidesKey
from fideslang.parse import parse_manifest


def get_server_resources(
    url: str, object_type: str, existing_keys: List[FidesKey], headers: Dict[str, str]
) -> List[FidesModel]:
    """
    Get a list of objects from the server that match the provided keys.
    """
    raw_server_object_list: Iterable[Dict] = filter(
        None,
        [
            api.find(url, object_type, key, headers).json().get("data")
            for key in existing_keys
        ],
    )
    server_object_list: List[FidesModel] = [
        parse_manifest(object_type, _object, from_server=True)
        for _object in raw_server_object_list
    ]
    return server_object_list
