"""This module handles anything related to working with raw manifest files."""
import os
from functools import reduce
from typing import Dict, List, Set

import yaml


def write_manifest(file_name: str, manifest: Dict) -> None:
    """
    Write a Python dict out to a yaml file.
    """
    with open(file_name, "w") as manifest_file:
        yaml.dump(manifest, manifest_file, sort_keys=False, indent=2)


def load_yaml_into_dict(file_path: str) -> Dict:
    """
    This loads yaml files into a dictionary to be used in API calls.
    """
    with open(file_path, "r") as yaml_file:
        return yaml.load(yaml_file, Loader=yaml.FullLoader)


def union_manifests(manifests: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Combine all of the manifests into a single dictionary,
    appending object values with the same keys.
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
    Ingest all of the manifests available in a directory and concatenate
    them into a single object.
    """
    manifest_list = [
        manifests_dir + "/" + file
        for file in os.listdir(manifests_dir)
        if "." in file and file.split(".")[1] in ["yml", "yaml"]
    ]
    loaded_manifests = [load_yaml_into_dict(file) for file in manifest_list]
    unioned_manifests = union_manifests(loaded_manifests)
    return unioned_manifests
