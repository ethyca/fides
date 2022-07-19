# pylint: disable=missing-docstring, redefined-outer-name
import os
from typing import Generator, List

import pytest
from fideslang.models import System, SystemMetadata
from py._path.local import LocalPath

from fidesctl.connectors.models import OktaConfig
from fidesctl.core import api
from fidesctl.core import system as _system
from fidesctl.core.config import FidesctlConfig


def create_server_systems(test_config: FidesctlConfig, systems: List[System]) -> None:
    for system in systems:
        api.create(
            url=test_config.cli.server_url,
            resource_type="system",
            json_resource=system.json(exclude_none=True),
            headers=test_config.user.request_headers,
        )


def delete_server_systems(test_config: FidesctlConfig, systems: List[System]) -> None:
    for system in systems:
        api.delete(
            url=test_config.cli.server_url,
            resource_type="system",
            resource_id=system.fides_key,
            headers=test_config.user.request_headers,
        )


@pytest.fixture(scope="function")
def create_test_server_systems(
    test_config: FidesctlConfig, redshift_systems: List[System]
) -> Generator:
    systems = redshift_systems
    delete_server_systems(test_config, systems)
    create_server_systems(test_config, systems)
    yield
    delete_server_systems(test_config, systems)


@pytest.fixture(scope="function")
def create_external_server_systems(test_config: FidesctlConfig) -> Generator:
    systems = _system.generate_redshift_systems(
        organization_key="default_organization",
        aws_config={},
    ) + _system.generate_rds_systems(
        organization_key="default_organization",
        aws_config={},
    )
    delete_server_systems(test_config, systems)
    create_server_systems(test_config, systems)
    yield
    delete_server_systems(test_config, systems)


@pytest.fixture()
def redshift_describe_clusters() -> Generator:
    describe_clusters = {
        "Clusters": [
            {
                "ClusterIdentifier": "redshift-cluster-1",
                "Endpoint": {
                    "Address": "redshift-cluster-1.c2angfh5kpo4.us-east-1.redshift.amazonaws.com",
                    "Port": 5439,
                },
                "ClusterNamespaceArn": "arn:aws:redshift:us-east-1:910934740016:namespace:057d5b0e-7eaa-4012-909c-3957c7149176",
            },
            {
                "ClusterIdentifier": "redshift-cluster-2",
                "Endpoint": {
                    "Address": "redshift-cluster-2.c2angfh5kpo4.us-east-1.redshift.amazonaws.com",
                    "Port": 5439,
                },
                "ClusterNamespaceArn": "arn:aws:redshift:us-east-1:910934740016:namespace:057d5b0e-7eaa-4012-909c-3957c7149177",
            },
        ]
    }
    yield describe_clusters


@pytest.fixture()
def redshift_systems() -> Generator:
    redshift_systems = [
        System(
            fides_key="redshift-cluster-1",
            organization_fides_key="default_organization",
            name="redshift-cluster-1",
            description="Fides Generated Description for Redshift Cluster: redshift-cluster-1",
            fidesctl_meta=SystemMetadata(
                endpoint_address="redshift-cluster-1.c2angfh5kpo4.us-east-1.redshift.amazonaws.com",
                endpoint_port="5439",
                resource_id="arn:aws:redshift:us-east-1:910934740016:namespace:057d5b0e-7eaa-4012-909c-3957c7149176",
            ),
            system_type="redshift_cluster",
            privacy_declarations=[],
        ),
        System(
            fides_key="redshift-cluster-2",
            organization_fides_key="default_organization",
            name="redshift-cluster-2",
            description="Fides Generated Description for Redshift Cluster: redshift-cluster-2",
            fidesctl_meta=SystemMetadata(
                endpoint_address="redshift-cluster-2.c2angfh5kpo4.us-east-1.redshift.amazonaws.com",
                endpoint_port="5439",
                resource_id="arn:aws:redshift:us-east-1:910934740016:namespace:057d5b0e-7eaa-4012-909c-3957c7149177",
            ),
            system_type="redshift_cluster",
            privacy_declarations=[],
        ),
    ]
    yield redshift_systems


@pytest.fixture()
def rds_systems() -> Generator:
    rds_systems = [
        System(
            fides_key="database-2",
            organization_fides_key="default_organization",
            name="database-2",
            description="Fides Generated Description for RDS Cluster: database-2",
            fidesctl_meta=SystemMetadata(
                endpoint_address="database-2.cluster-ckrdpkkb4ukm.us-east-1.rds.amazonaws.com",
                endpoint_port="3306",
                resource_id="arn:aws:rds:us-east-1:910934740016:cluster:database-2",
            ),
            system_type="rds_cluster",
            privacy_declarations=[],
        ),
        System(
            fides_key="database-1",
            organization_fides_key="default_organization",
            name="database-1",
            description="Fides Generated Description for RDS Instance: database-1",
            fidesctl_meta=SystemMetadata(
                endpoint_address="database-1.ckrdpkkb4ukm.us-east-1.rds.amazonaws.com",
                endpoint_port="3306",
                resource_id="arn:aws:rds:us-east-1:910934740016:db:database-1",
            ),
            system_type="rds_instance",
            privacy_declarations=[],
        ),
    ]
    yield rds_systems


@pytest.fixture()
def rds_describe_clusters() -> Generator:
    describe_clusters = {
        "DBClusters": [
            {
                "DBClusterIdentifier": "database-2",
                "Endpoint": "database-2.cluster-ckrdpkkb4ukm.us-east-1.rds.amazonaws.com",
                "Port": 3306,
                "DBClusterArn": "arn:aws:rds:us-east-1:910934740016:cluster:database-2",
            },
        ]
    }
    yield describe_clusters


@pytest.fixture()
def rds_describe_instances() -> Generator:
    describe_instances = {
        "DBInstances": [
            {
                "DBInstanceIdentifier": "database-1",
                "Endpoint": {
                    "Address": "database-1.ckrdpkkb4ukm.us-east-1.rds.amazonaws.com",
                    "Port": 3306,
                },
                "DBInstanceArn": "arn:aws:rds:us-east-1:910934740016:db:database-1",
            },
        ]
    }
    yield describe_instances


@pytest.mark.unit
def test_get_system_resource_ids(redshift_systems: List[System]) -> None:
    expected_result = [
        "arn:aws:redshift:us-east-1:910934740016:namespace:057d5b0e-7eaa-4012-909c-3957c7149176",
        "arn:aws:redshift:us-east-1:910934740016:namespace:057d5b0e-7eaa-4012-909c-3957c7149177",
    ]
    actual_result = _system.get_system_resource_ids(redshift_systems)
    assert actual_result == expected_result


@pytest.mark.unit
def test_find_missing_systems(
    redshift_systems: List[System], rds_systems: List[System]
) -> None:
    source_systems = rds_systems + redshift_systems
    existing_systems = redshift_systems
    actual_result = _system.find_missing_systems(
        source_systems=source_systems, existing_systems=existing_systems
    )
    assert actual_result == rds_systems


@pytest.mark.integration
def test_get_all_server_systems(
    test_config: FidesctlConfig, create_test_server_systems: Generator
) -> None:
    actual_result = _system.get_all_server_systems(
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
        exclude_systems=[],
    )
    assert actual_result


@pytest.mark.external
def test_scan_system_aws_passes(
    test_config: FidesctlConfig, create_external_server_systems: Generator
) -> None:
    _system.scan_system_aws(
        coverage_threshold=100,
        manifest_dir="",
        organization_key="default_organization",
        aws_config=None,
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
    )


@pytest.mark.external
def test_generate_system_aws(tmpdir: LocalPath, test_config: FidesctlConfig) -> None:
    actual_result = _system.generate_system_aws(
        file_name=f"{tmpdir}/test_file.yml",
        include_null=False,
        organization_key="default_organization",
        aws_config=None,
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
    )
    assert actual_result


OKTA_ORG_URL = "https://dev-78908748.okta.com"


@pytest.mark.external
def test_generate_system_okta(tmpdir: LocalPath, test_config: FidesctlConfig) -> None:
    actual_result = _system.generate_system_okta(
        file_name=f"{tmpdir}/test_file.yml",
        include_null=False,
        organization_key="default_organization",
        okta_config=OktaConfig(
            orgUrl=OKTA_ORG_URL,
            token=os.environ["OKTA_CLIENT_TOKEN"],
        ),
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
    )
    assert actual_result


@pytest.mark.external
def test_scan_system_okta_success(
    tmpdir: LocalPath, test_config: FidesctlConfig
) -> None:
    file_name = f"{tmpdir}/test_file.yml"
    _system.generate_system_okta(
        file_name=file_name,
        include_null=False,
        organization_key="default_organization",
        okta_config=OktaConfig(
            orgUrl=OKTA_ORG_URL,
            token=os.environ["OKTA_CLIENT_TOKEN"],
        ),
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
    )
    _system.scan_system_okta(
        manifest_dir=file_name,
        okta_config=OktaConfig(
            orgUrl=OKTA_ORG_URL,
            token=os.environ["OKTA_CLIENT_TOKEN"],
        ),
        organization_key="default_organization",
        coverage_threshold=100,
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
    )
    assert True


@pytest.mark.external
def test_scan_system_okta_fail(tmpdir: LocalPath, test_config: FidesctlConfig) -> None:
    with pytest.raises(SystemExit):
        _system.scan_system_okta(
            manifest_dir="",
            okta_config=OktaConfig(
                orgUrl=OKTA_ORG_URL,
                token=os.environ["OKTA_CLIENT_TOKEN"],
            ),
            coverage_threshold=100,
            organization_key="default_organization",
            url=test_config.cli.server_url,
            headers=test_config.user.request_headers,
        )
