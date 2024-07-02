"""Module that adds functionality for resource filtering."""

from typing import Callable, List, Optional

from fideslang.models import Organization, System

IGNORE_RESOURCE_ARN_FILTER = "ignore_resource_arn"
AWS_RESOURCE_FILTERS: List[str] = [IGNORE_RESOURCE_ARN_FILTER]


def get_system_arn(system: System) -> Optional[str]:
    """
    Returns resource arn for System if it is defined
    """
    system_arn = (
        system.fidesctl_meta.resource_id
        if system.fidesctl_meta and system.fidesctl_meta.resource_id
        else None
    )
    return system_arn


def is_arn_filter_match(arn: str, filter_arn: str) -> bool:
    """
    Returns True if the given arn matches the filter pattern. In order
    for an arn to be a match, it must match each field separated by a
    colon(:). If the filter pattern contains an empty field, then it is
    treated as wildcard for that field.

    Examples:
    arn=abc:def:ghi   filter_arn=abc:def:ghi   #exact match returns True
    arn=abc:def:ghi   filter_arn=abc::ghi      #wildcarded match returns True
    """
    arn_split = arn.split(":")
    filter_arn_split = filter_arn.split(":")

    # arns of different field lenth are treated as mismatch
    if len(arn_split) != len(filter_arn_split):
        return False

    for i in range(0, len(arn_split), 1):
        # filter pattern with value defined can be considered for mismatch
        if filter_arn_split[i] and filter_arn_split[i] != arn_split[i]:
            return False
    return True


def ignore_resource_arn(systems: List[System], filter_value: str) -> List[System]:
    """
    Given a list of systems and a filter pattern, returns elements which
    are not excluded by the arn matchin filter
    """
    filtered_systems = []
    for system in systems:
        system_arn = get_system_arn(system=system)
        if not system_arn or not is_arn_filter_match(
            arn=system_arn, filter_arn=filter_value
        ):
            filtered_systems.append(system)
    return filtered_systems


def get_aws_system_filter_function(
    filter_type: str,
) -> Callable[[List[System], str], List[System]]:
    """
    Returns filter function for a given filter type. A filter function
    takes an input System list and returns a new list that excludes filter
    matches.
    """
    system_filter_functions = {
        IGNORE_RESOURCE_ARN_FILTER: ignore_resource_arn,
    }
    filter_function = system_filter_functions[filter_type]
    return filter_function


def filter_aws_systems(
    systems: List[System], organization: Organization
) -> List[System]:
    """
    Given an organization with resource filters, passes a list
    of Systems through each filter. Filter ordering is not important
    as filters can only exclude Systems. Filter type is used to deremine
    the filter function.
    """
    resource_filters = (
        organization.fidesctl_meta.resource_filters
        if organization.fidesctl_meta and organization.fidesctl_meta.resource_filters
        else []
    )
    filtered_systems = systems
    for resource_filter in resource_filters:
        filter_type = resource_filter.type
        if filter_type in AWS_RESOURCE_FILTERS:
            filter_function = get_aws_system_filter_function(resource_filter.type)
            filtered_systems = filter_function(filtered_systems, resource_filter.value)
    return filtered_systems
