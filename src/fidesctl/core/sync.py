"""This module handles the logic for syncing remote resource versions into their local file."""
from typing import Dict, List, Optional

import yaml
from fideslang.manifests import load_yaml_into_dict

from fidesctl.cli.utils import echo_green, print_divider
from fidesctl.core.api_helpers import get_server_resource, list_server_resources
from fidesctl.core.utils import get_manifest_list


def write_manifest_file(manifest_path: str, manifest: Dict) -> None:
    """
    Write a manifest file out.
    """
    with open(manifest_path, "w") as manifest_file:
        yaml.dump(manifest, manifest_file, sort_keys=False, indent=2)
    echo_green(f"Updated manifest file written out to: '{manifest_path}'")


def sync_existing_resources(
    manifests_dir: str, url: str, headers: Dict[str, str]
) -> List[str]:
    """
    Update all of the pre-existing local resources to match their
    state on the server.
    """
    manifest_path_list = get_manifest_list(manifests_dir)
    # Store and return the keys of resources that get synced here.
    existing_keys: List[str] = []

    print_divider()
    for manifest_path in manifest_path_list:
        print(f"Syncing file: '{manifest_path}'...")
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


def sync_missing_resources(
    manifest_path: str, url: str, headers: Dict[str, str], existing_keys: List[str]
) -> bool:
    """
    Writes all "system", "dataset" and "policy" resources out locally
    that currently only exist on the server.
    """

    print(f"Writing out new resources to file: '{manifest_path}'...")
    resources_to_sync = ["system", "dataset", "policies"]
    resource_manifest = {
        resource: list_server_resources(
            url=url,
            headers=headers,
            resource_type=resource,
            exclude_keys=existing_keys,
            raw=True,
        )
        for resource in resources_to_sync
    }

    # Write out the resources in a file
    write_manifest_file(manifest_path, resource_manifest)
    print_divider()
    return True


def sync(
    manifests_dir: str,
    url: str,
    headers: Dict[str, str],
    sync_new: Optional[str],
) -> None:
    """
    If a resource in a local file has a matching resource on the server,
    write the server version into the local file.

    If the 'all' flag is passed, additionally pull all other server resources
    into local files as well.
    """
    existing_keys = sync_existing_resources(manifests_dir, url, headers)

    if sync_new:
        sync_missing_resources(sync_new, url, headers, existing_keys)

    echo_green("Sync complete.")
