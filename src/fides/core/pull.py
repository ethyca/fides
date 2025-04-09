"""This module handles the logic for syncing remote resource versions into their local file."""

from typing import Any, Dict, List, Optional

import yaml
from fideslang import model_list
from fideslang.manifests import load_yaml_into_dict

from fides.common.utils import echo_green, echo_red, print_divider
from fides.core.api_helpers import get_server_resource, list_server_resources
from fides.core.utils import get_manifest_list

MODEL_LIST = model_list


def remove_nulls(obj: Any) -> Any:
    """
    Recursively remove all null values from dictionaries and lists.

    Args:
        obj: Any Python object (dict, list, etc.)

    Returns:
        The transformed data structure with null values removed
    """
    if isinstance(obj, list):
        # For lists: process each item and filter out None values
        return [remove_nulls(item) for item in obj if item is not None]

    if isinstance(obj, dict):
        # For dictionaries: process each key-value pair and filter out pairs with None values
        return {
            key: remove_nulls(value) for key, value in obj.items() if value is not None
        }

    # Return all other data types unchanged
    return obj


def write_manifest_file(manifest_path: str, manifest: Dict) -> None:
    """
    Write a manifest file out.
    """
    with open(manifest_path, "w", encoding="utf-8") as manifest_file:
        yaml.dump(manifest, manifest_file, sort_keys=False, indent=2)
    echo_green(f"Updated manifest file written out to: '{manifest_path}'")


def pull_existing_resources(
    manifests_dir: str,
    url: str,
    headers: Dict[str, str],
) -> List[str]:
    """
    Update all of the pre-existing local resources to match their
    state on the server.
    """
    manifest_path_list = get_manifest_list(manifests_dir)
    # Store and return the keys of resources that get pulled here.
    existing_keys: List[str] = []

    print_divider()
    for manifest_path in manifest_path_list:
        print(f"Pulling file: '{manifest_path}'...")
        manifest = load_yaml_into_dict(manifest_path)
        updated_manifest = {}

        for resource_type in manifest.keys():
            resource_list = manifest[resource_type]
            updated_resource_list = []

            for resource in resource_list:
                fides_key = resource["fides_key"]
                existing_keys.append(fides_key)

                server_resource = get_server_resource(
                    url, resource_type, fides_key, headers
                )

                if server_resource:
                    # Remove null values from the server resource
                    server_resource = remove_nulls(server_resource)
                    updated_resource_list.append(server_resource)
                    print(
                        f" - {resource_type.capitalize()} with fides_key: {fides_key} is being updated from the server..."
                    )
                else:
                    updated_resource_list.append(resource)

            updated_manifest[resource_type] = updated_resource_list
            write_manifest_file(manifest_path, updated_manifest)
        print_divider()

    return existing_keys


def pull_resource_by_key(
    manifests_dir: str,
    url: str,
    headers: Dict[str, str],
    fides_key: str,
    resource_type: str,
) -> None:
    """
    Pull a resource from the server by its fides_key and update the local manifest file if it exists,
    otherwise a new manifest file at {manifests_dir}/{resource_type}.yml
    """
    if manifests_dir[-1] == "/":
        manifests_dir = manifests_dir[:-1]
    manifest_path = f"{manifests_dir}/{fides_key}.yml"
    print(f"Pulling {resource_type} with fides_key: {fides_key}...", end="\n")
    server_resource = get_server_resource(url, resource_type, fides_key, headers)

    if server_resource:
        # Remove null values from the server resource
        server_resource = remove_nulls(server_resource)
        try:
            manifest = load_yaml_into_dict(manifest_path)
        except FileNotFoundError:
            print(
                f"Manifest file {manifest_path} does not already exist and will be created"
            )
            manifest = {}
        manifest[resource_type] = [server_resource]
        write_manifest_file(manifest_path, manifest)

    else:
        echo_red(
            f"{resource_type} with fides_key: {fides_key} not found on the server."
        )


def pull_missing_resources(
    manifest_path: str,
    url: str,
    headers: Dict[str, str],
    existing_keys: List[str],
) -> bool:
    """
    Writes all "system", "dataset" and "policy" resources out locally
    that currently only exist on the server.
    """

    print(f"Writing out new resources to file: '{manifest_path}'...")
    resource_manifest = {
        resource: list_server_resources(
            url=url,
            headers=headers,
            resource_type=resource,
            exclude_keys=existing_keys,
        )
        for resource in MODEL_LIST
    }

    # Remove null values from all resources
    for resource_type, resources in resource_manifest.items():
        resource_manifest[resource_type] = [
            remove_nulls(resource) for resource in (resources or [])
        ]

    resource_manifest = {
        key: value for key, value in resource_manifest.items() if value
    }

    # Write out the resources in a file
    write_manifest_file(manifest_path, resource_manifest)
    print_divider()
    return True


def pull(
    manifests_dir: str,
    url: str,
    headers: Dict[str, str],
    fides_key: Optional[str],
    resource_type: Optional[str],
    all_resources_file: Optional[str],
) -> None:
    """
    If a resource in a local file has a matching resource on the server,
    write the server version into the local file.

    If the 'all_resources_file' option is present, pull all other server resources
    into a local file.

    If only `fides_key` is provided, only that resource will be pulled.
    """

    if fides_key and resource_type:
        pull_resource_by_key(
            manifests_dir=manifests_dir,
            url=url,
            headers=headers,
            fides_key=fides_key,
            resource_type=resource_type,
        )
        echo_green("Pull complete.")
        return

    existing_keys = pull_existing_resources(
        manifests_dir=manifests_dir,
        url=url,
        headers=headers,
    )

    if all_resources_file:
        pull_missing_resources(
            manifest_path=all_resources_file,
            url=url,
            headers=headers,
            existing_keys=existing_keys,
        )

    echo_green("Pull complete.")
