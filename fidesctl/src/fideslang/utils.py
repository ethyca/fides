from typing import Dict, Optional

from fideslang import FidesModel, Taxonomy


def get_resource_by_fides_key(
    taxonomy: Taxonomy, fides_key: str
) -> Optional[Dict[str, FidesModel]]:
    "Get a specific resource from a taxonomy by its fides_key."

    return {
        resource_type: resource
        for resource_type in taxonomy.__fields_set__
        for resource in getattr(taxonomy, resource_type)
        if resource.fidesKey == fides_key
    } or None
