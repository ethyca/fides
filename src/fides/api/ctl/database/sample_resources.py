"""
Sample resources to use for seeding the database. These are loaded & parsed from
the sample project at src/fides/data/sample_project.

See load_sample_resources() in seed.py for usage.
"""
import yaml
from importlib.resources import files
from typing import Dict, List, Union
from fideslang.models import Dataset, Organization, Policy, System

import fides.data.sample_project


def load_sample_resources_from_project(
    strict: bool = False,
) -> Dict[str, List[Union[Dataset, Organization, Policy, System]]]:
    """
    Loads all the sample resource YAML files from the sample project by
    traversing through the sample_resources/ folder, inspecting each file, and
    parsing them into fideslang models.

    Returns a dictionary, grouped by resource type (e.g. Dataset, System...)

    NOTE: This only implements parsing for types we _currently_ expect to use in
    the sample project. If new types are added to the project, this will quietly
    ignore them unless strict=True is provided, which throws an error. We test
    the "strict" version of this in the integration tests to ensure this code
    doesn't fall out of date.
    """
    sample_resources_path = files(fides.data.sample_project).joinpath(
        "sample_resources/"
    )
    sample_resources_dict = {
        "dataset": [],
        "organization": [],
        "policy": [],
        "system": [],
    }
    for yaml_path in sample_resources_path.iterdir():
        with yaml_path.open("r") as file:
            yaml_dict = yaml.safe_load(file)
            if yaml_dict.get("dataset", []):
                datasets = [Dataset.parse_obj(e) for e in yaml_dict.get("dataset")]
                sample_resources_dict["dataset"].extend(datasets)
            elif yaml_dict.get("organization", []):
                organizations = [
                    Organization.parse_obj(e) for e in yaml_dict.get("organization")
                ]
                sample_resources_dict["organization"].extend(organizations)
            elif yaml_dict.get("policy", []):
                policies = [Policy.parse_obj(e) for e in yaml_dict.get("policy")]
                sample_resources_dict["policy"].extend(policies)
            elif yaml_dict.get("system", []):
                systems = [System.parse_obj(e) for e in yaml_dict.get("system")]
                sample_resources_dict["system"].extend(systems)
            else:
                if strict:
                    unknown_resource_keys = list(yaml_dict.keys())
                    raise NotImplementedError(
                        f"Unexpected sample resource type, keys={unknown_resource_keys}"
                    )
                # quietly ignore failures when strict=False, so we only fail during tests
    return sample_resources_dict
