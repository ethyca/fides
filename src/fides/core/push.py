"""This module handles the logic required for pushing manifest files to the server."""

from pprint import pprint
from typing import Dict, List, Tuple

from deepdiff import DeepDiff
from fideslang.models import FidesModel, Taxonomy

from fides.common.utils import echo_green, echo_red, handle_cli_response
from fides.core import api
from fides.core.api_helpers import get_server_resources


def sort_create_update(
    manifest_resource_list: List[FidesModel],
    server_resource_list: List[FidesModel],
    diff: bool = False,
) -> Tuple[List[FidesModel], List[FidesModel]]:
    """
    Check the contents of the resource lists and populate separate
    new lists for resource creation or updating.

    The `diff` flag will print out the differences between the
    server resources and the local resource files.
    """

    server_resource_dict = {
        server_resource.fides_key: server_resource
        for server_resource in server_resource_list
    }

    create_list, update_list = [], []
    for manifest_resource in manifest_resource_list:
        resource_key = manifest_resource.fides_key

        # Check if the resource's fides_key matches one from the server
        if resource_key in server_resource_dict.keys():
            server_resource = server_resource_dict[resource_key]

            if diff:
                resource_diff = DeepDiff(
                    manifest_resource.model_dump(mode="json"),
                    server_resource.model_dump(mode="json"),
                )
                if resource_diff:
                    print(
                        f"\nUpdated resource with fides_key: {manifest_resource.fides_key}"
                    )
                    pprint(resource_diff)

            update_list.append(manifest_resource)

        else:
            if diff:
                print(f"\nNew resource with fides_key: {manifest_resource.fides_key}")
                pprint(manifest_resource.model_dump(exclude_unset=True))
            create_list.append(manifest_resource)

    return create_list, update_list


def echo_results(action: str, resource_type: str, resource_count: int) -> None:
    """
    Echo out the results of the push.
    """
    echo_green(f"{action.upper()} {resource_count} {resource_type} resource(s).")


def get_orphan_datasets(taxonomy: Taxonomy) -> List:
    """
    Validate all datasets are referenced at least one time
    by comparing all datasets to a set of referenced datasets
    within a privacy declaration.

    Returns a list containing any orphan datasets.
    """
    referenced_datasets = set()
    datasets = set()

    referenced_datasets.update(
        [
            dataset_reference
            for resource in taxonomy.system or []
            for privacy_declaration in resource.privacy_declarations
            if privacy_declaration.dataset_references is not None
            for dataset_reference in privacy_declaration.dataset_references
        ]
    )

    datasets.update([resource.fides_key for resource in taxonomy.dataset or []])

    missing_datasets = list(datasets - referenced_datasets)

    return missing_datasets


def push(
    url: str,
    taxonomy: Taxonomy,
    headers: Dict[str, str],
    dry: bool = False,
    diff: bool = False,
) -> None:
    """
    Push the current manifest file state to the server.
    """

    missing_datasets = get_orphan_datasets(taxonomy)
    if len(missing_datasets) > 0:
        echo_red(
            "Orphan Dataset Warning: The following datasets are not found referenced on a System"
        )
        for dataset in missing_datasets:
            print(dataset)

    for resource_type in taxonomy.model_fields_set:
        print("-" * 10)
        print(f"Processing {resource_type} resource(s)...")
        resource_list = getattr(taxonomy, resource_type)

        if diff or dry:
            existing_keys = [resource.fides_key for resource in resource_list]
            server_resource_list = get_server_resources(
                url, resource_type, existing_keys, headers
            )

            # Determine which resources should be created, updated, or are unchanged
            create_list, update_list = sort_create_update(
                resource_list, server_resource_list, diff
            )

            if dry:
                echo_results("would create", resource_type, len(create_list))
                echo_results("would update", resource_type, len(update_list))
                continue

        handle_cli_response(
            api.upsert(
                headers=headers,
                resource_type=resource_type,
                url=url,
                resources=[
                    resource.model_dump(mode="json") for resource in resource_list
                ],
            ),
            verbose=False,
        )

        echo_results("pushed", resource_type, len(resource_list))

    print("-" * 10)
