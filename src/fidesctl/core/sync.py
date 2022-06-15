"""This module handles the logic for syncing remote resource versions into their local file."""
import glob
from typing import Dict, List

import yaml
from fideslang.manifests import load_yaml_into_dict

from fidesctl.core.api_helpers import get_server_resource


def get_manifest_list(manifests_dir: str) -> List[str]:
    """Get a list of manifest files from the manifest directory."""

    yml_endings = ["yml", "yaml"]
    manifest_list = []
    for yml_ending in yml_endings:
        manifest_list += glob.glob(f"{manifests_dir}/**/*.{yml_ending}", recursive=True)

    return manifest_list


def sync(manifests_dir: str, url: str, headers: Dict[str, str]) -> None:
    """Sync local files with their server versions."""

    manifest_path_list = get_manifest_list(manifests_dir)

    for manifest_path in manifest_path_list:
        manifest = load_yaml_into_dict(manifest_path)
        updated_manifest = {}

        for resource_type in manifest.keys():
            resource_list = manifest[resource_type]
            updated_resource_list = []

            for resource in resource_list:
                fides_key = resource["fides_key"]
                server_resource = get_server_resource(
                    url, resource_type, fides_key, headers
                )
                if server_resource:
                    updated_resource_list.append(server_resource)
                else:
                    updated_resource_list.append(resource)
            updated_manifest[resource_type] = updated_resource_list
        with open(manifest_path, "w") as manifest_file:
            yaml.dump(manifest, manifest_file, sort_keys=False, indent=2)
