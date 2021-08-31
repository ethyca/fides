"""
This module is responsible for calculating what resources are referenced
by each other and building a dependency graph of relationships.
"""

import inspect
from functools import reduce
from typing import Dict, List, Set

from fideslang.models.fides_model import FidesModel, FidesKey
from fideslang.models.taxonomy import Taxonomy
from fideslang.utils import get_resource_by_fides_key


def find_referenced_fides_keys(resource: FidesModel) -> Set[FidesKey]:
    """
    Use type-signature introspection to figure out which fields
    include the FidesKey type and return all of those values.
    """

    referenced_fides_keys: Set[FidesKey] = set()
    signature = inspect.signature(type(resource), follow_wrapped=True)
    parameter_values = signature.parameters.values()
    for parameter in parameter_values:
        parameter_value = resource.__getattribute__(parameter.name)
        if parameter.annotation == FidesKey and parameter_value:
            referenced_fides_keys.add(parameter_value)
        elif parameter.annotation == List[FidesKey] and parameter_value:
            referenced_fides_keys.update(resource.__getattribute__(parameter.name))

    return referenced_fides_keys


def get_referenced_keys(taxonomy: Taxonomy) -> List[FidesKey]:
    # TODO: Flatten every object's signature so nested references aren't missed

    referenced_keys: List[Set[FidesKey]] = [
        find_referenced_fides_keys(resource)
        for resource_type in taxonomy.__fields_set__
        for resource in getattr(taxonomy, resource_type)
    ]
    key_set: Set[FidesKey] = set(reduce(lambda x, y: x.union(y), referenced_keys))
    keys_not_in_taxonomy = [
        fides_key
        for fides_key in key_set
        if get_resource_by_fides_key(taxonomy, fides_key) is None
    ]
    return keys_not_in_taxonomy
