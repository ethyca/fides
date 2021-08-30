"""Module for evaluating systems and registries."""
from json.decoder import JSONDecodeError
from typing import Dict

import requests

from fidesctl.core import api
from fidesctl.core.utils import echo_red
from fideslang import FidesModel, manifests, parse


def check_eval_result(response: requests.Response) -> requests.Response:
    """
    Check for the result of the evaluation and flip
    the status_code to 500 if it isn't passing.
    """

    try:
        data = response.json()["data"]
        if (not "status" in data) or data["status"] != "PASS":
            response.status_code = 500
    except JSONDecodeError:
        pass
    return response


def evaluate(
    url: str,
    manifests_dir: str,
    headers: Dict[str, str],
    fides_key: str,
    object_type: str,
    message: str,
    dry: bool,
) -> requests.Response:
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
    eval_dict: Dict[str, FidesModel] = {
        object_type: parse.parse_manifest(object_type, _object)
        for object_type, object_list in filtered_manifests.items()
        for _object in object_list
        if _object["fidesKey"] == fides_key
    }
    if eval_dict == {}:
        echo_red(
            "Failed to find a system or registry with fidesKey: {}".format(fides_key)
        )
        raise SystemExit

    object_type = list(eval_dict.keys())[0]
    _object = list(eval_dict.values())[0]

    response = api.dry_evaluate(
        url=url,
        object_type=object_type,
        json_object=_object.json(exclude_none=True),
        headers=headers,
    )
    return check_eval_result(response)
