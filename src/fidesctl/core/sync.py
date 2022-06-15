"""This module handles the logic for syncing remote resource versions into their local file."""
import glob
from typing import Dict, List

import yaml
from click import echo
from fideslang.manifests import load_yaml_into_dict

from fidesctl.cli.utils import echo_green, print_divider
from fidesctl.core.api_helpers import get_server_resource
from fidesctl.core.utils import get_manifest_list


def sync(manifests_dir: str, url: str, headers: Dict[str, str]) -> None:
    """Sync local files with their server versions."""

    manifest_path_list = get_manifest_list(manifests_dir)

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
        with open(manifest_path, "w") as manifest_file:
            yaml.dump(updated_manifest, manifest_file, sort_keys=False, indent=2)
        echo_green(f"Updated manifest file written out to: '{manifest_path}'")
        print_divider()
    echo_green("Sync complete.")
