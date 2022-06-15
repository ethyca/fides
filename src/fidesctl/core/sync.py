"""This module handles the logic for syncing remote resource versions into their local file."""
import glob
from http import server
from typing import Dict, List


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
        for resource_type in manifest.keys():
            resource_list = manifest[resource_type]
            for resource in resource_list:
                fides_key = resource["fides_key"]
                server_resource = get_server_resource(
                    url, resource_type, fides_key, headers
                )
                manifest[resource_type][resource] = server_resource

                print(server_resource)
