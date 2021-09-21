"""
This module is responsible for calculating what resources are referenced
by each other and building a dependency graph of relationships.
"""

import inspect
from functools import reduce
from typing import List, Set, Dict

from pydantic import AnyHttpUrl

from fidesctl.core.api_helpers import get_server_resources
from fidesctl.core.utils import echo_red
from fideslang.models import FidesModel, FidesKey, Taxonomy
from fideslang.utils import get_resource_by_fides_key


def find_referenced_fides_keys(resource: FidesModel) -> Set[FidesKey]:
    """
    Use type-signature introspection to figure out which fields
    include the FidesKey type and return all of those values.

    Note that this finds _all_ fides_keys, including the resource's own fides_key
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


def get_referenced_missing_keys(taxonomy: Taxonomy) -> List[FidesKey]:
    """
    Iterate through the Taxonomy and create a set of all of the FidesKeys
    that are contained within it.
    """
    referenced_keys: List[Set[FidesKey]] = [
        find_referenced_fides_keys(resource)
        for resource_type in taxonomy.__fields_set__
        for resource in getattr(taxonomy, resource_type)
    ]
    key_set: Set[FidesKey] = set(
        reduce(lambda x, y: set().union(x).union(y), referenced_keys)
    )
    keys_not_in_taxonomy = [
        fides_key
        for fides_key in key_set
        if get_resource_by_fides_key(taxonomy, fides_key) is None
    ]
    return keys_not_in_taxonomy


def hydrate_missing_resources(
    url: AnyHttpUrl,
    headers: Dict[str, str],
    missing_resource_keys: List[FidesKey],
    dehydrated_taxonomy: Taxonomy,
) -> Taxonomy:
    """
    Query the server for all of the missing resource keys and
    hydrate a copy of the dehydrated taxonomy with them.
    """

    resources_found = 0
    for resource_name in dehydrated_taxonomy.__fields__:
        server_resources = get_server_resources(
            url=url,
            resource_type=resource_name,
            headers=headers,
            existing_keys=missing_resource_keys,
        )
        resources_found += len(server_resources)
        dehydrated_taxonomy.__setattr__(
            resource_name,
            getattr(dehydrated_taxonomy, resource_name) + server_resources,
        )
    if resources_found < len(missing_resource_keys):
        echo_red("Refereneced FidesKeys do not exist!")
        raise SystemExit()
    return dehydrated_taxonomy
