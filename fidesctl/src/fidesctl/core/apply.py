"""This module handles the logic required for applying manifest files to the server."""
from pprint import pprint
from typing import Dict, List, Tuple, Optional

from deepdiff import DeepDiff

from fidesctl.cli.utils import handle_cli_response
from fidesctl.core import api
from fidesctl.core.api_helpers import get_server_resources
from fidesctl.core.utils import echo_green
from fideslang import FidesModel, Taxonomy


def sort_create_update_unchanged(
    manifest_resource_list: List[FidesModel],
    server_resource_list: List[FidesModel],
    diff: bool = False,
) -> Tuple[List[FidesModel], List[FidesModel], List[FidesModel]]:
    """
    Check the contents of the resource lists and populate separate
    new lists for resource creation, updating, or no change.

    The `diff` flag will print out the differences between the server resources
    the local resource files.
    """
    server_resource_dict = {
        server_resource.fides_key: server_resource
        for server_resource in server_resource_list
    }

    create_list = []
    update_list = []
    unchanged_list = []
    for manifest_resource in manifest_resource_list:
        resource_key = manifest_resource.fides_key

        # Check if the resource's fides_key matches one from the server
        if resource_key in server_resource_dict.keys():
            server_resource = server_resource_dict[resource_key]

            if manifest_resource == server_resource:
                unchanged_list.append(manifest_resource)
            else:
                if diff:
                    print(
                        f"\nUpdated resource with fides_key: {manifest_resource.fides_key}"
                    )
                    pprint(DeepDiff(server_resource, manifest_resource))
                update_list.append(manifest_resource)

        else:
            if diff:
                print(f"\nNew resource with fides_key: {manifest_resource.fides_key}")
                pprint(manifest_resource)
            create_list.append(manifest_resource)

    return create_list, update_list, unchanged_list


def execute_create_update_unchanged(
    url: str,
    headers: Dict[str, str],
    resource_type: str,
    create_list: Optional[List[FidesModel]] = None,
    update_list: Optional[List[FidesModel]] = None,
    unchanged_list: Optional[List[FidesModel]] = None,
) -> None:
    """
    Create, update, or just log resources based on which list they're in.
    """
    create_list = create_list or []
    update_list = update_list or []

    for create_resource in create_list:
        handle_cli_response(
            api.create(
                url=url,
                headers=headers,
                resource_type=resource_type,
                json_resource=create_resource.json(exclude_none=True),
            ),
            verbose=False,
        )
    for update_resource in update_list:
        handle_cli_response(
            api.update(
                url=url,
                headers=headers,
                resource_type=resource_type,
                resource_id=update_resource.fides_key,
                json_resource=update_resource.json(exclude_none=True),
            ),
            verbose=False,
        )


def echo_results(action: str, resource_type: str, resource_list: List) -> None:
    """
    Echo out the results of the apply.
    """
    echo_green(f"{action.upper()} {len(resource_list)} {resource_type} resources.")


def apply(
    url: str,
    taxonomy: Taxonomy,
    headers: Dict[str, str],
    dry: bool = False,
    diff: bool = False,
) -> None:
    """
    Apply the current manifest file state to the server.
    Excludes systems and registries.
    """
    for resource_type in taxonomy.__fields_set__:
        # Doing some echos here to make a pretty output
        print("-" * 10)
        echo_green(f"Processing {resource_type} resources...")
        resource_list = getattr(taxonomy, resource_type)

        existing_keys = [resource.fides_key for resource in resource_list]
        server_resource_list = get_server_resources(
            url, resource_type, existing_keys, headers
        )

        # Determine which resources should be created, updated, or are unchanged
        create_list, update_list, unchanged_list = sort_create_update_unchanged(
            resource_list, server_resource_list, diff
        )

        if dry:
            echo_results("would create", resource_type, create_list)
            echo_results("would update", resource_type, update_list)
            echo_results("would skip", resource_type, unchanged_list)
        else:
            execute_create_update_unchanged(
                url,
                headers,
                resource_type,
                create_list,
                update_list,
                unchanged_list,
            )

            echo_results("created", resource_type, create_list)
            echo_results("updated", resource_type, update_list)
            echo_results("skipped", resource_type, unchanged_list)
    print("-" * 10)
