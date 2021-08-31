"""Module for evaluating systems and registries."""
from json.decoder import JSONDecodeError
from typing import Dict, Union, List, Optional
from fideslang.models.validation import FidesKey

import requests
from pydantic import AnyHttpUrl

from fidesctl.cli.utils import handle_cli_response
from fidesctl.core import api
from fideslang import Policy, System, Registry, FidesModel, Taxonomy
from fideslang.manifests import ingest_manifests
from fideslang.parse import load_manifests_into_taxonomy, parse_manifest
from fideslang.relationships import get_referenced_keys


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


def get_all_server_policies(
    url: AnyHttpUrl, headers: Dict[str, str], exclude: Optional[List[FidesKey]] = None
) -> List[FidesModel]:
    """
    Get a list of all of the Policies that exist on the server.

    If 'exclude' is passed those specific Policies won't be pulled from the server
    """

    exclude = exclude if exclude else []
    ls_response = handle_cli_response(
        api.ls(url=url, object_type="policy", headers=headers), verbose=False
    )
    policy_keys = [
        resource["fidesKey"]
        for resource in ls_response.json().get("data")
        if resource["fidesKey"] not in exclude
    ]
    raw_policy_list = [
        handle_cli_response(api.find(url, "policy", key, headers), verbose=False)
        .json()
        .get("data")
        for key in policy_keys
    ]
    policy_list = [parse_manifest("policy", resource) for resource in raw_policy_list]
    return policy_list


def hydrate_missing_resources(
    missing_resource_keys: Set[FidesKey], taxonomy: Taxonomy
) -> Taxonomy:
    """
    Query the server for all of the missing resource keys and hydrate the provided taxonomy with them.
    """


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

    # Get all of the policies to evaluate
    local_policy_keys = (
        [policy.fidesKey for policy in taxonomy.policy] if taxonomy.policy else None
    )
    policy_list = get_all_server_policies(url, headers, exclude=local_policy_keys)
    if taxonomy.policy:
        taxonomy.policy += policy_list
    else:
        taxonomy.policy == policy_list

    ## TODO: add logic to fetch any missing resources, this will require looping
    ## through each endpoint since we don't know what kind of object it refers to
    missing_resource_keys = get_referenced_keys(taxonomy)
    hydrated_taxonomy = hydrate_missing_resources(missing_resource_keys, taxonomy)

    ## TODO: evaluation logic
    ## How does a system know which policy to be evaluated against?
    for policy in taxonomy.policy:
        execute_evaluation(policy)

    ## TODO: If not dry, create an evaluation object and full send it
    if not dry:
        pass

    return
