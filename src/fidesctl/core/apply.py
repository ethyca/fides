"""This module handles the logic required for applying manifest files to the server."""
from json import loads
from pprint import pprint
from typing import Dict, List, Tuple

from deepdiff import DeepDiff

from fidesctl.cli.utils import handle_cli_response
from fidesctl.core import api
from fidesctl.core.api_helpers import get_server_resources
from fidesctl.core.utils import echo_green
from fideslang import FidesModel, Taxonomy


def sort_create_update(
    manifest_resource_list: List[FidesModel],
    server_resource_list: List[FidesModel],
    diff: bool = False,
) -> Tuple[List[FidesModel], List[FidesModel]]:
    """
    Check the contents of the resource lists and populate separate
    new lists for resource creation or updating.

    The `diff` flag will print out the differences between the
    server resources the local resource files.
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
                print(
                    f"\nUpdated resource with fides_key: {manifest_resource.fides_key}"
                )
                pprint(
                    DeepDiff(
                        manifest_resource.dict(exclude_unset=True),
                        server_resource.dict(exclude_unset=True),
                    )
                )

            update_list.append(manifest_resource)

        else:
            if diff:
                print(f"\nNew resource with fides_key: {manifest_resource.fides_key}")
                pprint(manifest_resource.dict(exclude_unset=True))
            create_list.append(manifest_resource)

    return create_list, update_list


def echo_results(action: str, resource_type: str, resource_count: int) -> None:
    """
    Echo out the results of the apply.
    """
    echo_green(f"{action.upper()} {resource_count} {resource_type} resource(s).")


def apply(
    url: str,
    taxonomy: Taxonomy,
    headers: Dict[str, str],
    dry: bool = False,
    diff: bool = False,
) -> None:
    """
    Apply the current manifest file state to the server.
    """

    for resource_type in taxonomy.__fields_set__:
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
                resources=[loads(resource.json()) for resource in resource_list],
            ),
            verbose=False,
        )

        echo_results("applied", resource_type, len(resource_list))

    print("-" * 10)
