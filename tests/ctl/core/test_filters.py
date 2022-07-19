# pylint: disable=missing-docstring, redefined-outer-name
from typing import Generator

import pytest
from fideslang.models import (
    Organization,
    OrganizationMetadata,
    ResourceFilter,
    System,
    SystemMetadata,
)

from fides.ctl.core import filters as _filters


@pytest.fixture()
def filter_systems(
    system_with_arn1: Generator, system_with_arn2: Generator
) -> Generator:
    systems = [system_with_arn1, system_with_arn2]
    yield systems


@pytest.fixture()
def system_with_arn1() -> Generator:
    system = System(
        fides_key="database-2",
        organization_fides_key="default_organization",
        name="database-2",
        fidesctl_meta=SystemMetadata(
            resource_id="arn:aws:rds:us-east-1:910934740016:cluster:database-2",
        ),
        system_type="rds_cluster",
        privacy_declarations=[],
    )
    yield system


@pytest.fixture()
def system_with_arn2() -> Generator:
    system = System(
        fides_key="database-3",
        organization_fides_key="default_organization",
        name="database-3",
        fidesctl_meta=SystemMetadata(
            resource_id="arn:aws:rds:us-east-1:910934740016:cluster:database-3",
        ),
        system_type="rds_cluster",
        privacy_declarations=[],
    )
    yield system


@pytest.fixture()
def system_with_no_arn() -> Generator:
    system = System(
        fides_key="database-2",
        organization_fides_key="default_organization",
        name="database-2",
        system_type="rds_cluster",
        privacy_declarations=[],
    )
    yield system


@pytest.fixture()
def organization_with_filter() -> Generator:
    system = Organization(
        fides_key="organization_with_filter",
        name="organization_with_filter",
        fidesctl_meta=OrganizationMetadata(
            resource_filters=[
                ResourceFilter(
                    type="ignore_resource_arn",
                    value="arn:aws:rds:us-east-1:910934740016:cluster:database-2",
                ),
            ]
        ),
    )
    yield system


@pytest.fixture()
def organization_with_no_filter() -> Generator:
    system = Organization(
        fides_key="organization_with_no_filter",
        name="organization_with_no_filter",
    )
    yield system


@pytest.mark.unit
def test_get_system_arn(system_with_arn1: Generator) -> None:
    actual_result = _filters.get_system_arn(system=system_with_arn1)
    assert actual_result == "arn:aws:rds:us-east-1:910934740016:cluster:database-2"


@pytest.mark.unit
def test_get_system_arn_no_arn(system_with_no_arn: Generator) -> None:
    actual_result = _filters.get_system_arn(system=system_with_no_arn)
    assert not actual_result


@pytest.mark.unit
def test_is_arn_filter_match_exact_match() -> None:
    arn = "arn:aws:rds:us-east-1:910934740016:cluster:database-2"
    actual_result = _filters.is_arn_filter_match(arn=arn, filter_arn=arn)
    assert actual_result


@pytest.mark.unit
def test_is_arn_filter_match_wildcard_match() -> None:
    arn = "arn:aws:rds:us-east-1:910934740016:cluster:database-2"
    filter_arn = "arn:aws:rds:us-east-1:910934740016:cluster:"
    actual_result = _filters.is_arn_filter_match(arn=arn, filter_arn=filter_arn)
    assert actual_result


@pytest.mark.unit
def test_is_arn_filter_match_mismatch() -> None:
    arn = "arn:aws:rds:us-east-1:910934740016:cluster:database-2"
    filter_arn = "arn:aws:rds:us-east-1:12345678:cluster:database-2"
    actual_result = _filters.is_arn_filter_match(arn=arn, filter_arn=filter_arn)
    assert not actual_result


@pytest.mark.unit
def test_ignore_resource_arn(
    filter_systems: Generator, system_with_arn2: Generator
) -> None:
    filter_value = "arn:aws:rds:us-east-1:910934740016:cluster:database-2"
    actual_result = _filters.ignore_resource_arn(
        systems=filter_systems, filter_value=filter_value
    )
    assert len(actual_result) == 1
    assert actual_result[0] == system_with_arn2


@pytest.mark.unit
def test_ignore_resource_arn_missing_arn(system_with_no_arn: Generator) -> None:
    filter_value = "arn:aws:rds:us-east-1:910934740016:cluster:database-2"
    actual_result = _filters.ignore_resource_arn(
        systems=[system_with_no_arn], filter_value=filter_value
    )
    assert len(actual_result) == 1
    assert actual_result[0] == system_with_no_arn


@pytest.mark.unit
def test_filter_aws_systems_arn_filter(
    filter_systems: Generator,
    system_with_arn2: Generator,
    organization_with_filter: Generator,
) -> None:
    actual_result = _filters.filter_aws_systems(
        systems=filter_systems, organization=organization_with_filter
    )
    assert len(actual_result) == 1
    assert actual_result[0] == system_with_arn2


@pytest.mark.unit
def test_filter_aws_systems_no_filter(
    filter_systems: Generator, organization_with_no_filter: Generator
) -> None:
    actual_result = _filters.filter_aws_systems(
        systems=filter_systems, organization=organization_with_no_filter
    )
    assert actual_result == filter_systems
