"""Module for evaluating systems and registries."""
from typing import Dict, List, Tuple

from fidesctl.core import api, manifests, parse
from fidesctl.core.models import FidesModel

from .utils import echo_green, echo_red


def evaluate(url: str, manifests_dir: str, fides_key: str = "") -> None:
    """
    Rate a registry against all of the policies within an organization.
    """
    ingested_manifests = manifests.ingest_manifests(manifests_dir)
    filtered_manifests = {
        key: value
        for key, value in ingested_manifests.items()
        if key in ["system", "registry"]
    }

    # Look for a matching fidesKey in the system/registry objects
    try:
        eval_dict: Dict[str, FidesModel] = {
            object_type: parse.parse_manifest(object_type, _object)
            for object_type, object_list in filtered_manifests.items()
            for _object in object_list
            if _object["fidesKey"] == fides_key
        }
        assert eval_dict != {}
    except AssertionError as err:
        echo_red(
            "Failed to find a system or registry with fidesKey: {}".format(fides_key)
        )
        raise SystemExit

    object_type = list(eval_dict.keys())[0]
    _object = list(eval_dict.values())[0]

    response = api.evaluate(
        url=url,
        object_type=object_type,
        json_object=_object.json(exclude_none=True),
    )

    return response
