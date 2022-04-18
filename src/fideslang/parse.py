"""
This module handles everything related to parsing resources into Pydantic models,
either from local files or the server.
"""
from typing import List, Dict

from fideslang import model_map, FidesModel, Taxonomy
from fidesctl.core.utils import echo_red


def parse_dict(
    resource_type: str, resource: Dict, from_server: bool = False
) -> FidesModel:
    """
    Parse an individual resource into its Python model.
    """
    resource_source = "server" if from_server else "manifest file"
    if resource_type not in list(model_map.keys()):
        echo_red(f"This resource type does not exist: {resource_type}")
        raise SystemExit(1)

    try:
        parsed_manifest = model_map[resource_type].parse_obj(resource)
    except Exception as err:
        echo_red(
            "Failed to parse {} from {}:\n{}".format(
                resource_type, resource_source, resource
            )
        )
        raise SystemExit(err)
    return parsed_manifest


def load_manifests_into_taxonomy(raw_manifests: Dict[str, List[Dict]]) -> Taxonomy:
    """
    Parse the raw resource manifests into resource resources.
    """
    taxonomy = Taxonomy.parse_obj(
        {
            resource_type: [
                parse_dict(resource_type, resource) for resource in resource_list
            ]
            for resource_type, resource_list in raw_manifests.items()
        }
    )
    return taxonomy
