"""Module for evaluating systems and registries."""
import pprint
from typing import Dict, List, Optional, Callable
from fideslang.models.evaluation import StatusEnum
from fideslang.models.policy import InclusionEnum
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


def compare_rule_to_declaration(
    rule_types: List[FidesKey],
    declaration_types: List[FidesKey],
    rule_inclusion: InclusionEnum,
) -> bool:
    "Compare the rules against the declarations to determine whether the rule is broken."
    inclusion_map: Dict[InclusionEnum, Callable] = {
        InclusionEnum.ANY: any,
        InclusionEnum.ALL: all,
        InclusionEnum.NONE: lambda x: not any(x),
    }

    matching_data_categories = [
        True for data_category in declaration_types if data_category in rule_types
    ]
    result = inclusion_map[rule_inclusion](matching_data_categories)
    return result


def execute_evaluation(taxonomy: Taxonomy) -> Evaluation:
    """
    Check stated constraints of the Privacy Policy against what is declared in
    a system or registry.
    """

    evaluation_detail_list = []
    for policy in taxonomy.policy:
        for rule in policy.rules:
            for system in taxonomy.system:
                for declaration in system.privacyDeclarations:
                    ## TODO: Check the stated dependent dataset field as well

                    data_category_result = compare_rule_to_declaration(
                        rule_types=rule.dataCategories.values,
                        declaration_types=declaration.dataCategories,
                        rule_inclusion=rule.dataCategories.inclusion,
                    )

                    # A declaration only has one data use, so it gets put in a list
                    data_use_result = compare_rule_to_declaration(
                        rule_types=rule.dataUses.values,
                        declaration_types=[declaration.dataUse],
                        rule_inclusion=rule.dataUses.inclusion,
                    )

                    data_subject_result = compare_rule_to_declaration(
                        rule_types=rule.dataSubjects.values,
                        declaration_types=declaration.dataSubjects,
                        rule_inclusion=rule.dataSubjects.inclusion,
                    )

                    data_qualifier_result = (
                        declaration.dataQualifier == rule.dataQualifier
                    )

                    if all(
                        [
                            data_category_result,
                            data_subject_result,
                            data_use_result,
                            data_qualifier_result,
                        ]
                    ):
                        evaluation_detail_list += [
                            "Declaration: ({}) of System: ({}) failed Rule: ({}) from Policy: ({})".format(
                                declaration.name,
                                system.fidesKey,
                                rule.name,
                                policy.fidesKey,
                            )
                        ]

    status_enum = (
        StatusEnum.FAIL if len(evaluation_detail_list) > 0 else StatusEnum.PASS
    )
    evaluation = Evaluation(status=status_enum, details=evaluation_detail_list)
    return evaluation


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

    evaluation = execute_evaluation(hydrated_taxonomy)
    evaluation.message = message

    ## TODO: If not dry, create an evaluation object and full send it
    ## This is waiting for the server to have an /evaluations endpoint
    if not dry:
        pass

    return evaluation
