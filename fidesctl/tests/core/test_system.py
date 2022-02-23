import pytest

from typing import List

from fidesctl.core import system as _system, api
from fideslang.models import System, SystemMetadata


@pytest.fixture(scope="function")
def create_server_systems(test_config, redshift_systems):
    for system in redshift_systems:
        api.delete(
            url=test_config.cli.server_url,
            resource_type="system",
            resource_id=system.fides_key,
            headers=test_config.user.request_headers,
        )
        api.create(
            url=test_config.cli.server_url,
            resource_type="system",
            json_resource=system.json(exclude_none=True),
            headers=test_config.user.request_headers,
        )
    yield
    for system in redshift_systems:
        api.delete(
            url=test_config.cli.server_url,
            resource_type="system",
            resource_id=system.fides_key,
            headers=test_config.user.request_headers,
        )


@pytest.fixture()
def redshift_describe_clusters():
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
def redshift_systems():
    redshift_systems = [
        System(
            fides_key="redshift-cluster-1",
            organization_fides_key="default_organization",
            name="redshift-cluster-1",
            description="Fides Generated Description for Cluster: redshift-cluster-1",
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
            name="redshift-cluster-1",
            description="Fides Generated Description for Cluster: redshift-cluster-1",
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


@pytest.mark.unit
def test_transform_redshift_systems(redshift_describe_clusters, redshift_systems):
    actual_result = _system.transform_redshift_systems(redshift_describe_clusters)
    assert actual_result == redshift_systems


@pytest.mark.unit
def test_get_redshift_arns(redshift_describe_clusters):
    expected_result = [
        "arn:aws:redshift:us-east-1:910934740016:namespace:057d5b0e-7eaa-4012-909c-3957c7149176",
        "arn:aws:redshift:us-east-1:910934740016:namespace:057d5b0e-7eaa-4012-909c-3957c7149177",
    ]
    actual_result = _system.get_redshift_arns(redshift_describe_clusters)
    assert actual_result == expected_result


@pytest.mark.unit
def test_scan_aws_systems():
    (
        scan_text_output,
        scanned_resource_count,
        missing_resource_count,
    ) = _system.scan_aws_systems(
        scan_system_functions=[
            lambda: ("Scanned Resource Type 1", ["arn1", "arn2", "arn3"]),
            lambda: ("Scanned Resource Type 2", ["arn4"]),
            lambda: ("Scanned Resource Type 3", ["arn5"]),
        ],
        existing_system_arns=["arn4", "arn3"],
    )
    assert scan_text_output
    assert scanned_resource_count == 5
    assert missing_resource_count == 3


@pytest.mark.integration
def test_get_all_server_systems(test_config, create_server_systems):
    actual_result = _system.get_all_server_systems(
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
        exclude_systems=[],
    )
    assert actual_result


@pytest.mark.external
def test_scan_system_aws_passes(test_config, create_server_systems):
    _system.scan_system_aws(
        coverage_threshold=100,
        manifest_dir="",
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
    )

@pytest.mark.external
def test_generate_system_aws(tmpdir):
    actual_result = _system.generate_system_aws(f"{tmpdir}/test_file.yml", False)
    assert actual_result
