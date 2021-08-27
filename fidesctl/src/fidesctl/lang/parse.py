"""
This module handles everything related to parsing models,
either from local files or the server.
"""
from typing import Dict

from pydantic import ValidationError

from fidesctl.lang import model_map, FidesModel
from fidesctl.core.utils import echo_red


def parse_manifest(
    object_type: str, _object: Dict, from_server: bool = False
) -> FidesModel:
    """
    Parse an individual object into its Python model.
    """
    object_source = "server" if from_server else "manifest file"
    try:
        parsed_manifest = model_map[object_type].parse_obj(_object)
    except ValidationError as err:
        echo_red(f"Failed to parse this object: {_object} with the following errors:")
        raise SystemExit(err) from err
    except KeyError as err:
        echo_red(f"This object type does not exist: {object_type}")
        raise SystemExit
    except Exception as err:
        echo_red(
            "Failed to parse {} from {} with fidesKey: {}".format(
                object_type, object_source, _object["fidesKey"]
            )
        )
        raise err
    return parsed_manifest
