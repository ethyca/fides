"""Module for evaluating policies."""
from typing import Dict, List, Optional, Callable, cast

import uuid
import time
from pydantic import AnyHttpUrl

from fidesctl.cli.utils import handle_cli_response, pretty_echo
from fidesctl.core import api
from fidesctl.core.api_helpers import get_server_resources, get_server_resource
from fidesctl.core.parse import parse
from fidesctl.core.utils import echo_green, echo_red
from fideslang.models import (
    ActionEnum,
    Evaluation,
    Dataset,
    StatusEnum,
    InclusionEnum,
    Policy,
    PolicyRule,
    PrivacyDeclaration,
    System,
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
            "Policy ({}) could not be found".format(evaluate_fides_key)
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
                    "Policy ({}) uses unsupported policy action ({}). Only REJECT is currently supported".format(
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
            echo_red(
                "Found missing key ({}) referenced in taxonomy".format(current_key)
            )
            raise SystemExit(1)
    return fides_key_parent_hierarchy


def compare_rule_to_declaration(
    rule_types: List[FidesKey],
    declaration_type_hierarchies: List[List[FidesKey]],
    rule_inclusion: InclusionEnum,
) -> bool:
    """
    Compare the list of fides_keys within the rule against the list
    of fides_keys hierarchies from the declaration and uses the rule's inclusion
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


def validate_fides_keys_exist_for_evaluation(
    taxonomy: Taxonomy,
    policy_rule: PolicyRule,
    data_subjects: List[str],
    data_categories: List[str],
    data_qualifier: str,
    data_use: str,
) -> None:
    """
    Validates that keys used in evaluations are valid in the taxonomy
    """
    missing_key_errors = []

    categories_keys = [category.fides_key for category in taxonomy.data_category]
    for missing_data_category in set(
        data_categories + policy_rule.data_categories.values
    ) - set(categories_keys):
        missing_key_errors.append(
            "Missing DataCategory ({})".format(missing_data_category)
        )

    subject_keys = [subject.fides_key for subject in taxonomy.data_subject]
    for missing_data_subject in set(
        data_subjects + policy_rule.data_subjects.values
    ) - set(subject_keys):
        missing_key_errors.append(
            "Missing DataSubject ({})".format(missing_data_subject)
        )

    qualifiers_keys = [qualifier.fides_key for qualifier in taxonomy.data_qualifier]
    for missing_data_qualifier in set(
        [data_qualifier, policy_rule.data_qualifier]
    ) - set(qualifiers_keys):
        missing_key_errors.append(
            "Missing DataQualifier ({})".format(missing_data_qualifier)
        )

    data_use_keys = [data_use.fides_key for data_use in taxonomy.data_use]
    for missing_data_use in set([data_use] + policy_rule.data_uses.values) - set(
        data_use_keys
    ):
        missing_key_errors.append("Missing DataUse ({})".format(missing_data_use))

    if missing_key_errors:
        echo_red(
            "Found missing keys referenced in taxonomy \n{}".format(
                "\n ".join(missing_key_errors)
            )
        )
        raise SystemExit(1)


def evaluate_policy_rule(
    taxonomy: Taxonomy,
    policy_rule: PolicyRule,
    data_subjects: List[str],
    data_categories: List[str],
    data_qualifier: str,
    data_use: str,
) -> bool:
    """
    Given data subjects, data categories, data qualifier and data use,
    builds hierarchies of applicable types and evaluates the result of a
    policy rule
    """
    validate_fides_keys_exist_for_evaluation(
        taxonomy=taxonomy,
        policy_rule=policy_rule,
        data_subjects=data_subjects,
        data_categories=data_categories,
        data_qualifier=data_qualifier,
        data_use=data_use,
    )

    category_hierarchies = [
        get_fides_key_parent_hierarchy(
            taxonomy=taxonomy, fides_key=declaration_category
        )
        for declaration_category in data_categories
    ]
    data_category_result = compare_rule_to_declaration(
        rule_types=policy_rule.data_categories.values,
        declaration_type_hierarchies=category_hierarchies,
        rule_inclusion=policy_rule.data_categories.inclusion,
    )

    # A declaration only has one data use, so its hierarchy gets put in a list
    data_use_hierarchies = [
        get_fides_key_parent_hierarchy(taxonomy=taxonomy, fides_key=data_use)
    ]
    data_use_result = compare_rule_to_declaration(
        rule_types=policy_rule.data_uses.values,
        declaration_type_hierarchies=data_use_hierarchies,
        rule_inclusion=policy_rule.data_uses.inclusion,
    )

    # A data subject does not have a hierarchical structure
    data_subject_result = compare_rule_to_declaration(
        rule_types=policy_rule.data_subjects.values,
        declaration_type_hierarchies=[[data_subject] for data_subject in data_subjects],
        rule_inclusion=policy_rule.data_subjects.inclusion,
    )

    data_qualifier_result = (
        policy_rule.data_qualifier
        in get_fides_key_parent_hierarchy(taxonomy=taxonomy, fides_key=data_qualifier)
    )

    evaluation_result = all(
        [
            data_category_result,
            data_subject_result,
            data_use_result,
            data_qualifier_result,
        ]
    )
    return evaluation_result


def get_dataset_by_fides_key(taxonomy: Taxonomy, fides_key: str) -> Optional[Dataset]:
    """
    Returns a dataset within the taxonomy for a given fides key
    """
    dataset = next(
        iter(
            [dataset for dataset in taxonomy.dataset if dataset.fides_key == fides_key]
        ),
        None,
    )
    return cast(Dataset, dataset)


def evaluate_dataset_reference(
    taxonomy: Taxonomy,
    policy: Policy,
    system: System,
    policy_rule: PolicyRule,
    privacy_declaration: PrivacyDeclaration,
    dataset: Dataset,
) -> List[str]:
    """
    Evaluates the contraints of a given rule and dataset that was referenced
    from a given privacy declaration
    """
    evaluation_detail_list = []
    if dataset.data_categories:
        dataset_result = evaluate_policy_rule(
            taxonomy=taxonomy,
            policy_rule=policy_rule,
            data_subjects=privacy_declaration.data_subjects,
            data_categories=dataset.data_categories,
            data_qualifier=dataset.data_qualifier,
            data_use=privacy_declaration.data_use,
        )

        if dataset_result:
            evaluation_detail_list += [
                "Declaration ({}) of System ({}) failed Rule ({}) from Policy ({}) for Dataset ({})".format(
                    privacy_declaration.name,
                    system.fides_key,
                    policy_rule.name,
                    policy.fides_key,
                    dataset.fides_key,
                )
            ]
    for collection in dataset.collections:
        if collection.data_categories:
            dataset_collection_result = evaluate_policy_rule(
                taxonomy=taxonomy,
                policy_rule=policy_rule,
                data_subjects=privacy_declaration.data_subjects,
                data_categories=collection.data_categories,
                data_qualifier=collection.data_qualifier,
                data_use=privacy_declaration.data_use,
            )

            if dataset_collection_result:
                evaluation_detail_list += [
                    "Declaration ({}) of System ({}) failed Rule ({}) from Policy ({}) for DatasetCollection ({})".format(
                        privacy_declaration.name,
                        system.fides_key,
                        policy_rule.name,
                        policy.fides_key,
                        collection.name,
                    )
                ]

        for field in collection.fields:
            if field.data_categories:
                field_result = evaluate_policy_rule(
                    taxonomy=taxonomy,
                    policy_rule=policy_rule,
                    data_subjects=privacy_declaration.data_subjects,
                    data_categories=field.data_categories,
                    data_qualifier=field.data_qualifier,
                    data_use=privacy_declaration.data_use,
                )

                if field_result:
                    evaluation_detail_list += [
                        "Declaration ({}) of System ({}) failed Rule ({}) from Policy ({}) for DatasetField ({})".format(
                            privacy_declaration.name,
                            system.fides_key,
                            policy_rule.name,
                            policy.fides_key,
                            field.name,
                        )
                    ]
    return evaluation_detail_list


def evaluate_privacy_declaration(
    taxonomy: Taxonomy,
    policy: Policy,
    system: System,
    policy_rule: PolicyRule,
    privacy_declaration: PrivacyDeclaration,
) -> List[str]:
    """
    Evaluates the contraints of a given rule and privacy declaration. This
    includes additional data set references
    """
    evaluation_detail_list = []
    declaration_result = evaluate_policy_rule(
        taxonomy=taxonomy,
        policy_rule=policy_rule,
        data_subjects=privacy_declaration.data_subjects,
        data_categories=privacy_declaration.data_categories,
        data_qualifier=privacy_declaration.data_qualifier,
        data_use=privacy_declaration.data_use,
    )

    if declaration_result:
        evaluation_detail_list += [
            "Declaration ({}) of System ({}) failed Rule ({}) from Policy ({})".format(
                privacy_declaration.name,
                system.fides_key,
                policy_rule.name,
                policy.fides_key,
            )
        ]

    for dataset_reference in privacy_declaration.dataset_references or []:
        dataset = get_dataset_by_fides_key(
            taxonomy=taxonomy, fides_key=dataset_reference
        )
        if dataset:
            evaluation_detail_list += evaluate_dataset_reference(
                taxonomy=taxonomy,
                policy=policy,
                system=system,
                policy_rule=policy_rule,
                privacy_declaration=privacy_declaration,
                dataset=dataset,
            )
        else:
            echo_red(
                "Dataset ({}) referenced in Declaration ({}) could not be found in taxonomy".format(
                    dataset_reference, privacy_declaration.name
                )
            )
            raise SystemExit(1)
    return evaluation_detail_list


def execute_evaluation(taxonomy: Taxonomy) -> Evaluation:
    """
    Check the stated constraints of each Privacy Policy's rules against
    each system's privacy declarations.
    """
    evaluation_detail_list = []
    for policy in taxonomy.policy:
        for rule in policy.rules:
            for system in taxonomy.system:
                for declaration in system.privacy_declarations:

                    evaluation_detail_list += evaluate_privacy_declaration(
                        taxonomy=taxonomy,
                        policy=policy,
                        system=system,
                        policy_rule=rule,
                        privacy_declaration=declaration,
                    )
    status_enum = (
        StatusEnum.FAIL if len(evaluation_detail_list) > 0 else StatusEnum.PASS
    )
    new_uuid = str(uuid.uuid4()).replace("-", "_")
    timestamp = str(time.time()).split(".")[0]
    generated_key = f"{new_uuid}_{timestamp}"
    evaluation = Evaluation(
        fides_key=generated_key,
        status=status_enum,
        details=evaluation_detail_list,
    )
    return evaluation


def populate_referenced_keys(
    taxonomy: Taxonomy,
    url: AnyHttpUrl,
    headers: Dict[str, str],
    last_keys: List[FidesKey],
) -> Taxonomy:
    """
    Takes in a taxonomy with potentially missing references to fides keys.
    Populates any missing fides_keys recursively and returns the populated taxonomy.

    Recursively calls itself after every hydration to make sure there are no new missing keys.
    """
    missing_resource_keys = get_referenced_missing_keys(taxonomy)
    if missing_resource_keys and set(missing_resource_keys) != set(last_keys):
        taxonomy = hydrate_missing_resources(
            url=url,
            headers=headers,
            missing_resource_keys=missing_resource_keys,
            dehydrated_taxonomy=taxonomy,
        )
        return populate_referenced_keys(
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
    populate_referenced_keys(taxonomy=taxonomy, url=url, headers=headers, last_keys=[])

    echo_green("Executing evaluations...")
    evaluation = execute_evaluation(taxonomy)
    evaluation.message = message
    if not dry:
        echo_green("Sending the evaluation results to the server...")
        response = api.create(
            url=url,
            resource_type="evaluation",
            json_resource=evaluation.json(exclude_none=True),
            headers=headers,
        )
        handle_cli_response(response, verbose=False)

    if evaluation.status == "FAIL":
        pretty_echo(evaluation.dict(), color="red")
        raise SystemExit(1)
    echo_green("Evaluation passed!")

    return evaluation
