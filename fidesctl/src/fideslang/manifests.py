"""This module handles anything related to working with raw manifest files."""
import glob
from functools import reduce
from typing import Dict, List, Set, Union

import yaml
from fidesctl.core.utils import echo_red


def write_manifest(
    file_name: str, manifest: Union[List, Dict], resource_type: str
) -> None:
    """
    Write a dict representation of a resource out to a file.
    """
    if isinstance(manifest, dict):
        manifest = {resource_type: [manifest]}
    else:
        manifest = {resource_type: manifest}

    with open(file_name, "w") as manifest_file:
        yaml.dump(manifest, manifest_file, sort_keys=False, indent=2)


def load_yaml_into_dict(file_path: str) -> Dict:
    """
    This loads yaml files into a dictionary to be used in API calls.
    """
    with open(file_path, "r") as yaml_file:
        loaded = yaml.safe_load(yaml_file)
        if isinstance(loaded, dict):
            return loaded

    echo_red(f"Failed to parse invalid manifest: {file_path.split('/')[-1]}. Skipping.")
    return {}


def filter_manifest_by_type(
    manifests: Dict[str, List], filter_types: List[str]
) -> Dict[str, List]:
    "Filter the resources so that only the specified resource types are returned."
    return {key: value for key, value in manifests.items() if key in filter_types}


def union_manifests(manifests: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Combine all of the manifests into a single dictionary,
    appending resource values with the same keys.
    """

    key_lists: List[List[str]] = [list(manifest.keys()) for manifest in manifests]
    key_set: Set[str] = set(reduce(lambda x, y: [*x, *y], key_lists))

    unioned_dict: Dict[str, List] = {}
    for manifest in manifests:
        for key in key_set:
            if key in manifest.keys() and key in unioned_dict.keys():
                unioned_dict[key] += manifest[key]
            elif key in manifest.keys():
                unioned_dict[key] = manifest[key]
    return unioned_dict


def ingest_manifests(manifests_dir: str) -> Dict[str, List[Dict]]:
    """
    Ingest either a single file or all of the manifests available in a
    directory and concatenate them into a single object.

    Directories will be searched recursively.
    """
    yml_endings = ["yml", "yaml"]
    if manifests_dir.split(".")[-1] in yml_endings:
        manifests = load_yaml_into_dict(manifests_dir)

    else:
        manifest_list = []
        for yml_ending in yml_endings:
            manifest_list += glob.glob(
                f"{manifests_dir}/**/*.{yml_ending}", recursive=True
            )

        manifests = union_manifests(
            [load_yaml_into_dict(file) for file in manifest_list]
        )
    return manifests
