"""
This module handles everything related to parsing models,
either from local files or the server.
"""
from typing import Dict

from .models import MODEL_DICT, FidesModel
from .utils import echo_red


def parse_manifest(
    object_type: str, _object: Dict, from_server: bool = False
) -> FidesModel:
    """
    Parse an individual object into its Python model.
    """
    object_source = "server" if from_server else "manifest file"
    try:
        parsed_manifest = MODEL_DICT[object_type].parse_obj(_object)
    except Exception as err:
        echo_red(
            "Failed to parse {} from {} with fidesKey: {}".format(
                object_type, object_source, _object["fidesKey"]
            )
        )
        raise SystemExit(err) from err
    return parsed_manifest
