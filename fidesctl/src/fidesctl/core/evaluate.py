"""Module for evaluating systems and registries."""
from json.decoder import JSONDecodeError
from typing import Set, Dict, Union, List, Optional
from fideslang.models.validation import FidesKey

import requests
from pydantic import AnyHttpUrl

from fidesctl.cli.utils import handle_cli_response
from fidesctl.core import api
from fidesctl.core.api_helpers import get_server_resources
from fideslang import Policy, Evaluation, Taxonomy
from fideslang.manifests import ingest_manifests
from fideslang.parse import load_manifests_into_taxonomy
from fideslang.relationships import (
    get_referenced_missing_keys,
    hydrate_missing_resources,
)


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


def get_all_server_policies(
    url: AnyHttpUrl, headers: Dict[str, str], exclude: Optional[List[FidesKey]] = None
) -> List[Policy]:
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
    policy_list = get_server_resources(
        url=url, object_type="policy", headers=headers, existing_keys=policy_keys
    )
    return policy_list


def execute_evaluation(taxonomy: Taxonomy) -> Evaluation:
    """
    Check stated constraints of the Privacy Policy against what is declared in
    a system or registry.
    """
    pass


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

    missing_resource_keys = get_referenced_missing_keys(taxonomy)
    hydrated_taxonomy = hydrate_missing_resources(
        url=url,
        headers=headers,
        missing_resource_keys=missing_resource_keys,
        dehydrated_taxonomy=taxonomy,
    )

    ## TODO: evaluation logic
    ## How does a system know which policy to be evaluated against?
    execute_evaluation(hydrated_taxonomy)

    ## TODO: If not dry, create an evaluation object and full send it
    ## This is waiting for the server to have an /evaluations endpoint
    if not dry:
        pass

    return
