"""Module for evaluating policies."""

import uuid
from typing import Callable, Dict, List, Optional, Set, cast

from fideslang.default_taxonomy import DEFAULT_TAXONOMY
from fideslang.models import (
    Dataset,
    Evaluation,
    MatchesEnum,
    Policy,
    PolicyRule,
    PrivacyDeclaration,
    StatusEnum,
    System,
    Taxonomy,
    Violation,
    ViolationAttributes,
)
from fideslang.relationships import get_referenced_missing_keys
from fideslang.utils import get_resource_by_fides_key
from fideslang.validation import FidesKey
from pydantic import AnyHttpUrl

from fides.common.utils import echo_green, echo_red, handle_cli_response, pretty_echo
from fides.core import api
from fides.core.api_helpers import get_server_resource, get_server_resources
from fides.core.parse import parse
from fides.core.utils import get_all_level_fields


def get_evaluation_policies(
    local_policies: List[Policy],
    evaluate_fides_key: Optional[str],
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
        assert isinstance(server_policy_found, Policy)
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
    return policy_list  # type: ignore[return-value]


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
        fides_key_parent_hierarchy.append(FidesKey(current_key))
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
    rule_match: MatchesEnum,
) -> Set[str]:
    """
    Compare the list of fides_keys within the rule against the list
    of fides_keys hierarchies from the declaration and uses the rule's matches
    field to determine whether the rule is triggered or not. Returns the offending
    keys, prioritizing the first descendant in the hierarchy.
    """
    matched_declaration_types = set()
    mismatched_declaration_types = set()
    for declaration_type_hierarchy in declaration_type_hierarchies:
        declared_declaration_type = declaration_type_hierarchy[0]
        if len(set(declaration_type_hierarchy).intersection(set(rule_types))) > 0:
            matched_declaration_types.add(declared_declaration_type)
        else:
            mismatched_declaration_types.add(declared_declaration_type)

    matches_map: Dict[MatchesEnum, Callable] = {
        # any matches return matching declared values as violations
        MatchesEnum.ANY: lambda: matched_declaration_types,
        # all matches return matching declared values as violations if all values match rule values
        MatchesEnum.ALL: lambda: (
            matched_declaration_types
            if len(matched_declaration_types) == len(declaration_type_hierarchies)
            else set()
        ),
        # none matches return mismatched declared values as violations if none of the values matched rule values
        MatchesEnum.NONE: lambda: (
            mismatched_declaration_types
            if not any(matched_declaration_types)
            else set()
        ),
        # other matches return mismatched declared values as violations
        MatchesEnum.OTHER: lambda: mismatched_declaration_types,
    }

    return matches_map[rule_match]()


def evaluate_policy_rule(
    taxonomy: Taxonomy,
    policy_rule: PolicyRule,
    data_subjects: List[str],
    data_categories: List[str],
    data_use: str,
    declaration_violation_message: str,
) -> List[Violation]:
    """
    Given data subjects, data categories and data use,
    builds hierarchies of applicable types and evaluates the result of a
    policy rule
    """
    category_hierarchies = [
        get_fides_key_parent_hierarchy(
            taxonomy=taxonomy, fides_key=declaration_category
        )
        for declaration_category in data_categories
    ]
    data_category_violations = compare_rule_to_declaration(
        rule_types=policy_rule.data_categories.values,
        declaration_type_hierarchies=category_hierarchies,
        rule_match=policy_rule.data_categories.matches,
    )

    # A declaration only has one data use, so its hierarchy gets put in a list
    data_use_hierarchies = [
        get_fides_key_parent_hierarchy(taxonomy=taxonomy, fides_key=data_use)
    ]
    data_use_violations = compare_rule_to_declaration(
        rule_types=policy_rule.data_uses.values,
        declaration_type_hierarchies=data_use_hierarchies,
        rule_match=policy_rule.data_uses.matches,
    )

    # A data subject does not have a hierarchical structure
    data_subject_violations = compare_rule_to_declaration(
        rule_types=policy_rule.data_subjects.values,
        declaration_type_hierarchies=[
            [FidesKey(data_subject)] for data_subject in data_subjects
        ],
        rule_match=policy_rule.data_subjects.matches,
    )

    evaluation_result = all(
        [
            data_category_violations,
            data_use_violations,
            data_subject_violations,
        ]
    )

    if evaluation_result:
        violations = [
            Violation(
                detail="{}. Violated usage of data categories ({}) for data uses ({}) and subjects ({})".format(
                    declaration_violation_message,
                    ",".join(data_category_violations),
                    ",".join(data_use_violations),
                    ",".join(data_subject_violations),
                ),
                violating_attributes=ViolationAttributes(
                    data_categories=list(data_category_violations),
                    data_uses=list(data_use_violations),
                    data_subjects=list(data_subject_violations),
                ),
            )
        ]
        return violations
    return []


def get_dataset_by_fides_key(taxonomy: Taxonomy, fides_key: str) -> Optional[Dataset]:
    """
    Returns a dataset within the taxonomy for a given fides key
    """
    taxonomy.dataset = getattr(taxonomy, "dataset") or []
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
) -> List[Violation]:
    """
    Evaluates the constraints of a given rule and dataset that was referenced
    from a given privacy declaration
    """
    evaluation_violation_list = []
    if dataset.data_categories:
        dataset_violation_message = "Declaration ({}) of system ({}) failed rule ({}) from policy ({}) for dataset ({})".format(
            privacy_declaration.name,
            system.fides_key,
            policy_rule.name,
            policy.fides_key,
            dataset.fides_key,
        )

        dataset_result_violations = evaluate_policy_rule(
            taxonomy=taxonomy,
            policy_rule=policy_rule,
            data_subjects=[str(x) for x in privacy_declaration.data_subjects],
            data_categories=[str(x) for x in dataset.data_categories],
            data_use=privacy_declaration.data_use,
            declaration_violation_message=dataset_violation_message,
        )

        evaluation_violation_list += dataset_result_violations

    for collection in dataset.collections:
        collection_violation_message = "Declaration ({}) of system ({}) failed rule ({}) from policy ({}) for dataset collection ({})".format(
            privacy_declaration.name,
            system.fides_key,
            policy_rule.name,
            policy.fides_key,
            collection.name,
        )

        if collection.data_categories:
            dataset_collection_result_violations = evaluate_policy_rule(
                taxonomy=taxonomy,
                policy_rule=policy_rule,
                data_subjects=[str(x) for x in privacy_declaration.data_subjects],
                data_categories=[str(x) for x in collection.data_categories],
                data_use=privacy_declaration.data_use,
                declaration_violation_message=collection_violation_message,
            )

            evaluation_violation_list += dataset_collection_result_violations

        for field in get_all_level_fields(collection.fields):
            field_violation_message = "Declaration ({}) of system ({}) failed rule ({}) from policy ({}) for dataset field ({})".format(
                privacy_declaration.name,
                system.fides_key,
                policy_rule.name,
                policy.fides_key,
                field.name,
            )

            if field.data_categories:
                field_result_violations = evaluate_policy_rule(
                    taxonomy=taxonomy,
                    policy_rule=policy_rule,
                    data_subjects=[str(x) for x in privacy_declaration.data_subjects],
                    data_categories=[str(x) for x in field.data_categories],
                    data_use=privacy_declaration.data_use,
                    declaration_violation_message=field_violation_message,
                )

                evaluation_violation_list += field_result_violations

    return evaluation_violation_list


def evaluate_privacy_declaration(
    taxonomy: Taxonomy,
    policy: Policy,
    system: System,
    policy_rule: PolicyRule,
    privacy_declaration: PrivacyDeclaration,
) -> List[Violation]:
    """
    Evaluates the contraints of a given rule and privacy declaration. This
    includes additional data set references
    """
    evaluation_violation_list = []

    declaration_violation_message = (
        "Declaration ({}) of system ({}) failed rule ({}) from policy ({})".format(
            privacy_declaration.name,
            system.fides_key,
            policy_rule.name,
            policy.fides_key,
        )
    )

    declaration_result_violations = evaluate_policy_rule(
        taxonomy=taxonomy,
        policy_rule=policy_rule,
        data_subjects=[str(x) for x in privacy_declaration.data_subjects],
        data_categories=[str(x) for x in privacy_declaration.data_categories],
        data_use=privacy_declaration.data_use,
        declaration_violation_message=declaration_violation_message,
    )

    evaluation_violation_list += declaration_result_violations

    for dataset_reference in privacy_declaration.dataset_references or []:
        dataset = get_dataset_by_fides_key(
            taxonomy=taxonomy, fides_key=dataset_reference
        )
        if dataset:
            evaluation_violation_list += evaluate_dataset_reference(
                taxonomy=taxonomy,
                policy=policy,
                system=system,
                policy_rule=policy_rule,
                privacy_declaration=privacy_declaration,
                dataset=dataset,
            )
        else:
            echo_red(
                "Dataset ({}) referenced in declaration ({}) could not be found in taxonomy".format(
                    dataset_reference, privacy_declaration.name
                )
            )
            raise SystemExit(1)
    return evaluation_violation_list


def execute_evaluation(taxonomy: Taxonomy) -> Evaluation:
    """
    Check the stated constraints of each Privacy Policy's rules against
    each system's privacy declarations.
    """
    evaluation_violation_list = []
    taxonomy.policy = getattr(taxonomy, "policy") or []
    taxonomy.system = getattr(taxonomy, "system") or []
    for policy in taxonomy.policy:
        for rule in policy.rules:
            for system in taxonomy.system:
                for declaration in system.privacy_declarations:
                    evaluation_violation_list += evaluate_privacy_declaration(
                        taxonomy=taxonomy,
                        policy=policy,
                        system=system,
                        policy_rule=rule,
                        privacy_declaration=declaration,
                    )
    status_enum = (
        StatusEnum.FAIL if len(evaluation_violation_list) > 0 else StatusEnum.PASS
    )
    new_uuid = str(uuid.uuid4()).replace("-", "_")
    evaluation = Evaluation(
        fides_key=FidesKey(new_uuid),
        status=status_enum,
        violations=evaluation_violation_list,
    )
    return evaluation


def hydrate_missing_resources(
    url: AnyHttpUrl,
    headers: Dict[str, str],
    missing_resource_keys: List[FidesKey],
    dehydrated_taxonomy: Taxonomy,
) -> Taxonomy:
    """
    Query the server for all of the missing resource keys and
    hydrate a copy of the dehydrated taxonomy with them.
    """

    for resource_name in dehydrated_taxonomy.__fields__:
        server_resources = get_server_resources(
            url=url,
            resource_type=resource_name,
            headers=headers,
            existing_keys=missing_resource_keys,
        )
        setattr(
            dehydrated_taxonomy,
            resource_name,
            getattr(dehydrated_taxonomy, resource_name) + server_resources,
        )
    return dehydrated_taxonomy


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
    missing_resource_keys = list(get_referenced_missing_keys(taxonomy))
    keys_not_found = set(last_keys).intersection(set(missing_resource_keys))
    if keys_not_found:
        echo_red(f"Missing resource keys: {keys_not_found}")
        raise SystemExit(1)

    if missing_resource_keys:
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


def merge_taxonomies(
    primary_taxonomy: Taxonomy, secondary_taxonomy: Taxonomy
) -> Taxonomy:
    """
    Merges the secondary_taxonomy into the primary_taxonomy while
    preserving all of the existing keys within the primary_taxonomy.
    """
    for resource_name in primary_taxonomy.__fields__:
        # Get the unique set of keys we want to include in the merged taxonomy
        primary_keys = [
            resource.fides_key for resource in getattr(primary_taxonomy, resource_name)
        ]
        secondary_resources = [
            resource
            for resource in getattr(secondary_taxonomy, resource_name)
            if resource.fides_key not in primary_keys
        ]
        # Create a list of all of the resources to go in the merged taxonomy
        resource_list = getattr(primary_taxonomy, resource_name) + secondary_resources
        setattr(primary_taxonomy, resource_name, resource_list)

    return primary_taxonomy


def evaluate(
    url: AnyHttpUrl,
    manifests_dir: str,
    headers: Dict[str, str],
    policy_fides_key: str = "",
    message: str = "",
    local: bool = False,
    dry: bool = False,
) -> Evaluation:
    """
    Perform evaluation for a given Policy. If a policy key is not
    provided, perform an evaluation for all of the Policies in an organzation

    Local Policy definition files will be used as opposed to their
    server-definitions if available.
    """

    # Merge the User-defined taxonomy & Default Taxonomy
    user_taxonomy = parse(manifests_dir)
    taxonomy = merge_taxonomies(user_taxonomy, DEFAULT_TAXONOMY)

    # Determine which Policies will be evaluated
    policies = taxonomy.policy
    assert policies, "At least one Policy must be present"
    if not local:
        # Append server-side Policies if not running in local_mode
        policies = get_evaluation_policies(
            local_policies=policies,
            evaluate_fides_key=policy_fides_key,
            url=url,
            headers=headers,
        )

    validate_policies_exist(policies=policies, evaluate_fides_key=policy_fides_key)
    echo_green(
        "Evaluating the following policies:\n- {}".format(
            "\n- ".join([key.fides_key for key in policies])
        )
    )
    print("-" * 10)

    echo_green("Checking for missing resources...")
    missing_resources = get_referenced_missing_keys(taxonomy)
    if local and missing_resources:
        echo_red(str(missing_resources))
        echo_red("Not all referenced resources exist locally!")
        raise SystemExit(1)
    populate_referenced_keys(taxonomy=taxonomy, url=url, headers=headers, last_keys=[])

    echo_green("Executing Policy evaluation(s)...")
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
