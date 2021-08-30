"""Module for evaluating systems and registries."""
import inspect
from json.decoder import JSONDecodeError
from typing import Dict, List, Optional

import requests

from fidesctl.core import api
from fidesctl.core.utils import echo_red
from fideslang import FidesModel, Taxonomy
from fideslang.manifests import ingest_manifests
from fideslang.parse import load_manifests_into_taxonomy, parse_manifest
from fideslang.relationships import find_referenced_fides_keys


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


def get_resource_by_fides_key(
    taxonomy: Taxonomy, fides_key: str
) -> Optional[Dict[str, FidesModel]]:
    "Get a specific resource from a taxonomy by its fides_key."

    return {
        object_type: parse_manifest(object_type, resource)
        for object_type, object_list in taxonomy.dict(
            exclude_none=True, by_alias=True
        ).items()
        for resource in object_list
        if resource["fidesKey"] == fides_key
    } or None


def evaluate(
    url: str,
    manifests_dir: str,
    headers: Dict[str, str],
    fides_key: str,
    message: str,
    dry: bool,
) -> requests.Response:
    """
    Rate a registry against all of the policies within an organization.
    """
    ingested_manifests = ingest_manifests(manifests_dir)
    taxonomy = load_manifests_into_taxonomy(ingested_manifests)
    filtered_taxonomy = taxonomy.copy(include={"systems", "registries"})

    resource_to_evaluate = get_resource_by_fides_key(filtered_taxonomy, fides_key)
    if not resource_to_evaluate:
        echo_red(
            "Failed to find a system or registry with fidesKey: {}".format(fides_key)
        )
        raise SystemExit

    object_type = list(resource_to_evaluate.keys())[0]
    resource = list(resource_to_evaluate.values())[0]

    find_referenced_fides_keys(resource)

    ## TODO: evaluation logic

    ## TODO: If not dry, create an evaluation object and full send it

    return
