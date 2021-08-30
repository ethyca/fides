import inspect
from typing import Dict, List

from fideslang.models.fides_model import FidesModel, FidesKey


def find_referenced_fides_keys(resource: FidesModel) -> List[FidesKey]:
    """
    Use type-signature introspection to figure out which fields
    include the FidesKey type and return all of those values.
    """

    referenced_fides_keys: List = []
    signature = inspect.signature(type(resource))
    for parameter in signature.parameters.values():
        if parameter.annotation == FidesKey:
            referenced_fides_keys += [resource.__getattribute__(parameter.name)]

    print(referenced_fides_keys)
    return
