"""Module for evaluating systems and registries."""
from json.decoder import JSONDecodeError
from typing import Dict, Union, List, Optional
from fideslang.models.validation import FidesKey

import requests
from pydantic import AnyHttpUrl

from fidesctl.cli.utils import handle_cli_response
from fidesctl.core import api
from fidesctl.core.utils import echo_red
from fideslang import Policy, System, Registry
from fideslang.manifests import ingest_manifests
from fideslang.parse import load_manifests_into_taxonomy, parse_manifest
from fideslang.relationships import get_referenced_keys
from fideslang.utils import get_resource_by_fides_key


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


def execute_evaluation(policy: Policy, resource: Union[System, Registry]) -> bool:
    """
    Check stated constraints of the Privacy Policy against what is declared in
    a system or registry.
    """


def get_all_policies(
    url: AnyHttpUrl, headers: Dict[str, str], exclude: Optional[List[FidesKey]] = None
) -> List[Policy]:
    """
    Get a list of all of the Policies that exist on the server.

    If 'exclude' is passed those specific Policies won't be pulled from the server
    """

    ls_response = handle_cli_response(
        api.ls(url=url, object_type="policy", headers=headers), verbose=False
    )
    policy_keys = [resource["fidesKey"] for resource in ls_response.json().get("data")]
    raw_policy_list = [
        handle_cli_response(api.find(url, "policy", key, headers), verbose=False)
        .json()
        .get("data")
        for key in policy_keys
    ]
    print(raw_policy_list)
    policy_list = [parse_manifest("policy", resource) for resource in raw_policy_list]
    print(policy_list)
    return policy_list


def evaluate(
    url: AnyHttpUrl,
    manifests_dir: str,
    fides_key: str,
    headers: Dict[str, str],
    message: str,
    dry: bool,
) -> requests.Response:
    """
    Rate a registry against all of the policies within an organization.
    """
    ingested_manifests = ingest_manifests(manifests_dir)
    taxonomy = load_manifests_into_taxonomy(ingested_manifests)

    ## TODO: get all of the policies loaded locally
    ## Default to using local policies first before loading from the server
    policy_list = get_all_policies(url, headers)

    # Need to reparse instead of just copy so the __fields_set__ attr is correct
    filtered_taxonomy = taxonomy.parse_obj(
        taxonomy.dict(include={"system", "registry"})
    )

    resource_to_evaluate = get_resource_by_fides_key(filtered_taxonomy, fides_key)
    if not resource_to_evaluate:
        echo_red(
            "Failed to find a system or registry with fidesKey: {}".format(fides_key)
        )
        raise SystemExit

    missing_resource_keys = get_referenced_keys(taxonomy)

    ## TODO: add logic to fetch any missing resources, this will require looping
    ## through each endpoint since we don't know what kind of object it refers to

    ## TODO: evaluation logic
    ## How does a system know which policy to be evaluated against?
    execute_evaluation(taxonomy.policy[0])

    ## TODO: If not dry, create an evaluation object and full send it

    return
