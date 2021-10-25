"""Module for evaluating policies."""
from typing import Dict, List, Optional, Callable

from pydantic import AnyHttpUrl

from fidesctl.cli.utils import handle_cli_response, pretty_echo
from fidesctl.core import api
from fidesctl.core.api_helpers import get_server_resources, get_server_resource
from fidesctl.core.parse import parse
from fidesctl.core.utils import echo_green, echo_red
from fideslang.models import (
    ActionEnum,
    Evaluation,
    PolicyRule,
    StatusEnum,
    InclusionEnum,
    Policy,
    Taxonomy,
)
from fideslang.validation import FidesKey
from fideslang.relationships import (
    get_referenced_missing_keys,
    hydrate_missing_resources,
)
from fideslang.utils import get_resource_by_fides_key


def get_evaluation_policies(
    local_policies: List[Policy],
    evaluate_fides_key: str,
    url: AnyHttpUrl,
    headers: Dict[str, str],
) -> List[Policy]:
    """
    Returns policies to be evaluated. If 'evaluate_fides_key' is
    passed then only that policy will be returned. Otherwise, returns
    all policies.
    """
    if evaluate_fides_key:
        local_policy_found = next(
            filter(
                lambda policy: policy.fides_key == evaluate_fides_key, local_policies
            ),
            None,
        )
        if local_policy_found:
            return [local_policy_found]

        server_policy_found = get_server_resource(
            url=url,
            resource_type="policy",
            resource_key=evaluate_fides_key,
            headers=headers,
        )
        return [server_policy_found] if server_policy_found else []

    local_policy_keys = (
        [policy.fides_key for policy in local_policies] if local_policies else None
    )
    all_policies = local_policies + get_all_server_policies(
        url=url, headers=headers, exclude=local_policy_keys
    )
    return all_policies


def get_all_server_policies(
    url: AnyHttpUrl, headers: Dict[str, str], exclude: Optional[List[FidesKey]] = None
) -> List[Policy]:
    """
    Get a list of all of the Policies that exist on the server.

    If 'exclude' is passed those specific Policies won't be pulled from the server.
    """

    exclude = exclude if exclude else []
    ls_response = handle_cli_response(
        api.ls(url=url, resource_type="policy", headers=headers), verbose=False
    )
    policy_keys = [
        resource["fides_key"]
        for resource in ls_response.json()
        if resource["fides_key"] not in exclude
    ]
    policy_list = get_server_resources(
        url=url, resource_type="policy", headers=headers, existing_keys=policy_keys
    )
    return policy_list


def validate_policies_exist(policies: List[Policy], evaluate_fides_key: str) -> None:
    """
    Validates that policies to be evaluated exist. If no policies were found
    raises an error and logs an error.
    """
    if not policies:
        echo_red(
            "Policy {} could not be found".format(evaluate_fides_key)
            if evaluate_fides_key
            else "No Policies found to evaluate"
        )
        raise SystemExit(1)


def validate_supported_policy_rules(policies: List[Policy]) -> None:
    """
    Validates that only supported actions are used in taxonomy. Currently
    evaluations only support REJECT policy actions.
    see: https://github.com/ethyca/fides/issues/150
    """
    for policy in policies:
        for rule in policy.rules:
            if rule.action != ActionEnum.REJECT:
                echo_red(
                    "Policy {} uses unsupported policy action {}. Only REJECT is currently supported".format(
                        policy.name, rule.action
                    )
                )
                raise SystemExit(1)


def get_fides_key_parent_hierarchy(
    taxonomy: Taxonomy, fides_key: str
) -> List[FidesKey]:
    """
    Traverses a hierarchy of parents for a given fides key and returns
    the hierarchy starting with the given fides key.
    """
    current_key = fides_key
    fides_key_parent_hierarchy = []
    while True:
        fides_key_parent_hierarchy.append(current_key)
        found_resource_map = get_resource_by_fides_key(
            taxonomy=taxonomy, fides_key=current_key
        )
        if found_resource_map:
            found_resource = list(found_resource_map.values())[-1]
            if found_resource and "parent_key" in found_resource.__fields_set__:
                current_key = getattr(found_resource, "parent_key")
                if not current_key:
                    break
            else:
                break
        else:
            break
    return fides_key_parent_hierarchy


def compare_rule_to_declaration(
    rule_types: List[FidesKey],
    declaration_type_hierarchies: List[List[FidesKey]],
    rule_inclusion: InclusionEnum,
) -> bool:
    """
    Compare the list of fides_keys within the rule against the list
    of fides_keys hierarchies from the declaration and use the rule's inclusion
    field to determine whether the rule is triggered or not.
    """
    inclusion_map: Dict[InclusionEnum, Callable] = {
        InclusionEnum.ANY: any,
        InclusionEnum.ALL: all,
        InclusionEnum.NONE: lambda x: not any(x),
    }

    matching_data_categories = [
        bool(len(set(data_category_hierarchy).intersection(set(rule_types))) > 0)
        for data_category_hierarchy in declaration_type_hierarchies
    ]
    result = inclusion_map[rule_inclusion](matching_data_categories)
    return result


def execute_evaluation(taxonomy: Taxonomy) -> Evaluation:
    """
    Check the stated constraints of each Privacy Policy's rules against
    what is declared each system's privacy declarations.
    """

    evaluation_detail_list = []
    for policy in taxonomy.policy:
        for rule in policy.rules:
            for system in taxonomy.system:
                for declaration in system.privacy_declarations:

                    category_hierarchies = [
                        get_fides_key_parent_hierarchy(
                            taxonomy=taxonomy, fides_key=declaration_category
                        )
                        for declaration_category in declaration.data_categories
                    ]
                    data_category_result = compare_rule_to_declaration(
                        rule_types=rule.data_categories.values,
                        declaration_type_hierarchies=category_hierarchies,
                        rule_inclusion=rule.data_categories.inclusion,
                    )

                    # A declaration only has one data use, so its hierarchy gets put in a list
                    data_use_hierarchies = [
                        get_fides_key_parent_hierarchy(
                            taxonomy=taxonomy, fides_key=declaration.data_use
                        )
                    ]
                    data_use_result = compare_rule_to_declaration(
                        rule_types=rule.data_uses.values,
                        declaration_type_hierarchies=data_use_hierarchies,
                        rule_inclusion=rule.data_uses.inclusion,
                    )

                    # A data subject does not have a hierarchical structure
                    data_subject_result = compare_rule_to_declaration(
                        rule_types=rule.data_subjects.values,
                        declaration_type_hierarchies=[
                            [data_subject] for data_subject in declaration.data_subjects
                        ],
                        rule_inclusion=rule.data_subjects.inclusion,
                    )

                    data_qualifier_result = (
                        rule.data_qualifier
                        in get_fides_key_parent_hierarchy(
                            taxonomy=taxonomy, fides_key=declaration.data_qualifier
                        )
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
                            "Declaration ({}) of System ({}) failed Rule ({}) from Policy ({})".format(
                                declaration.name,
                                system.fides_key,
                                rule.name,
                                policy.fides_key,
                            )
                        ]

    status_enum = (
        StatusEnum.FAIL if len(evaluation_detail_list) > 0 else StatusEnum.PASS
    )
    evaluation = Evaluation(status=status_enum, details=evaluation_detail_list)
    return evaluation


def populate_references_keys(
    taxonomy: Taxonomy,
    url: AnyHttpUrl,
    headers: Dict[str, str],
    last_keys: List[FidesKey],
) -> Taxonomy:
    """
    Takes in a taxonomy with potentially missing references to fides keys.
    Populates any missing fides_keys recursively and returns the populated taxonomy.
    """
    missing_resource_keys = get_referenced_missing_keys(taxonomy)
    # Not all fides keys can be pulled from the server, we will
    # check if the last recursive run added any additional keys to the set
    if missing_resource_keys and set(missing_resource_keys) != set(last_keys):
        # TODO: Need to figure out how to log this even though being invoked recursively
        echo_green(
            "Fetching the following missing resources from the server:\n- {}".format(
                "\n".join(missing_resource_keys)
            )
        )
        taxonomy = hydrate_missing_resources(
            url=url,
            headers=headers,
            missing_resource_keys=missing_resource_keys,
            dehydrated_taxonomy=taxonomy,
        )
        return populate_references_keys(
            taxonomy=taxonomy, url=url, headers=headers, last_keys=missing_resource_keys
        )
    return taxonomy


def evaluate(
    url: AnyHttpUrl,
    manifests_dir: str,
    fides_key: str,
    headers: Dict[str, str],
    message: str,
    dry: bool,
) -> Evaluation:
    """
    Perform evaluation for a given Policy. If a policy key is not
    provided, perform an evaluation for all of the Policies in an organzation

    Local Policy definition files will be used as opposed to their
    server-definitions if available.
    """
    taxonomy = parse(manifests_dir)

    # Populate all of the policies to evaluate
    taxonomy.policy = get_evaluation_policies(
        local_policies=taxonomy.policy,
        evaluate_fides_key=fides_key,
        url=url,
        headers=headers,
    )
    validate_policies_exist(policies=taxonomy.policy, evaluate_fides_key=fides_key)
    validate_supported_policy_rules(policies=taxonomy.policy)

    echo_green(
        "Evaluating the following policies:\n{}".format(
            "\n".join([key.fides_key for key in taxonomy.policy])
        )
    )
    print("-" * 10)

    echo_green("Checking for missing resources...")
    populate_references_keys(taxonomy=taxonomy, url=url, headers=headers, last_keys=[])

    echo_green("Executing evaluations...")
    evaluation = execute_evaluation(taxonomy)
    evaluation.message = message

    # TODO: add the evaluations endpoint to the API
    if not dry:
        echo_green("Sending the evaluation results to the server...")

    if evaluation.status == "FAIL":
        pretty_echo(evaluation.dict(), color="red")
        raise SystemExit(1)
    echo_green("Evaluation passed!")

    return evaluation
