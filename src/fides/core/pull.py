"""This module handles the logic for syncing remote resource versions into their local file."""
from typing import Dict, List, Optional

import yaml
from fideslang import model_list
from fideslang.manifests import load_yaml_into_dict

from fides.cli.utils import print_divider
from fides.core.api_helpers import get_server_resource, list_server_resources
from fides.core.utils import echo_green, get_manifest_list

MODEL_LIST = model_list


def write_manifest_file(manifest_path: str, manifest: Dict) -> None:
    """
    Write a manifest file out.
    """
    with open(manifest_path, "w", encoding="utf-8") as manifest_file:
        yaml.dump(manifest, manifest_file, sort_keys=False, indent=2)
    echo_green(f"Updated manifest file written out to: '{manifest_path}'")


def pull_existing_resources(
    manifests_dir: str, url: str, headers: Dict[str, str]
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
                    url, resource_type, fides_key, headers, raw=True
                )

                if server_resource:
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
            raw=True,
        )
        for resource in MODEL_LIST
    }

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
    all_resources_file: Optional[str],
) -> None:
    """
    If a resource in a local file has a matching resource on the server,
    write the server version into the local file.

    If the 'all_resources_file' option is present, pull all other server resources
    into a local file.
    """
    existing_keys = pull_existing_resources(
        manifests_dir=manifests_dir, url=url, headers=headers
    )

    if all_resources_file:
        pull_missing_resources(
            manifest_path=all_resources_file,
            url=url,
            headers=headers,
            existing_keys=existing_keys,
        )

    echo_green("Pull complete.")
