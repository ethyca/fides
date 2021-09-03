"""
This module handles everything related to parsing models,
either from local files or the server.
"""
from typing import List, Dict

from pydantic import ValidationError

from fideslang import model_map, FidesModel, Taxonomy
from fidesctl.core.utils import echo_red


def parse_manifest(
    object_type: str, resource: Dict, from_server: bool = False
) -> FidesModel:
    """
    Parse an individual object into its Python model.
    """
    object_source = "server" if from_server else "manifest file"
    try:
        parsed_manifest = model_map[object_type].parse_obj(resource)
    except ValidationError as err:
        echo_red(f"Failed to parse this object: {resource} with the following errors:")
        raise SystemExit(err) from err
    except KeyError as err:
        echo_red(f"This object type does not exist: {object_type}")
        raise SystemExit
    except Exception as err:
        echo_red(
            "Failed to parse {} from {} with fidesKey: {}".format(
                object_type, object_source, resource["fidesKey"]
            )
        )
        raise err
    return parsed_manifest


def load_manifests_into_taxonomy(raw_manifests: Dict[str, List[Dict]]) -> Taxonomy:
    """
    Parse the raw resource manifests into resource objects.
    """

    taxonomy = Taxonomy.parse_obj(
        {
            object_type: [
                parse_manifest(object_type, _object) for _object in object_list
            ]
            for object_type, object_list in raw_manifests.items()
        }
    )
    return taxonomy
