# pylint: disable=missing-docstring, redefined-outer-name
import os
from typing import Generator

import pytest
from fideslang.models import System, SystemMetadata
from py._path.local import LocalPath

import fides.connectors.aws as aws_connector
from fides.config import FidesConfig
from fides.connectors.models import AWSConfig


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
            meta={},
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
            meta={},
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


def get_test_aws_config() -> AWSConfig:
    return AWSConfig(
        region_name=os.environ["AWS_DEFAULT_REGION"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    )


def get_test_aws_config_temporary_credentials() -> AWSConfig:
    # first get an STS client with our permanent credentials
    client = aws_connector.get_aws_client(
        service="sts", aws_config=get_test_aws_config()
    )
    # then use the STS client to get temporary credentials
    temporary_credentials = client.get_session_token()["Credentials"]
    # return an AWS config with the temporary credentials
    return AWSConfig(
        region_name=os.environ["AWS_DEFAULT_REGION"],
        aws_access_key_id=temporary_credentials["AccessKeyId"],
        aws_secret_access_key=temporary_credentials["SecretAccessKey"],
        aws_session_token=temporary_credentials["SessionToken"],
    )


@pytest.fixture()
def rds_systems() -> Generator:
    rds_systems = [
        System(
            fides_key="database-2",
            organization_fides_key="default_organization",
            name="database-2",
            description="Fides Generated Description for RDS Cluster: database-2",
            meta={},
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
            meta={},
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


# Unit
@pytest.mark.unit
def test_transform_redshift_systems(
    redshift_describe_clusters: Generator, redshift_systems: Generator
) -> None:
    actual_result = aws_connector.create_redshift_systems(
        describe_clusters=redshift_describe_clusters,
        organization_key="default_organization",
    )
    assert actual_result == redshift_systems


@pytest.mark.unit
def test_transform_rds_systems(
    rds_describe_clusters: Generator,
    rds_describe_instances: Generator,
    rds_systems: Generator,
) -> None:
    actual_result = aws_connector.create_rds_systems(
        describe_clusters=rds_describe_clusters,
        describe_instances=rds_describe_instances,
        organization_key="default_organization",
    )
    assert actual_result == rds_systems


# Integration
@pytest.mark.external
def test_describe_redshift_clusters(
    tmpdir: LocalPath, test_config: FidesConfig
) -> None:
    client = aws_connector.get_aws_client(
        service="redshift",
        aws_config=get_test_aws_config(),
    )
    actual_result = aws_connector.describe_redshift_clusters(client=client)
    assert actual_result


@pytest.mark.external
def test_describe_redshift_clusters_temporary_credentials(
    tmpdir: LocalPath, test_config: FidesConfig
) -> None:
    """
    Test temporary credential (session token) auth mechanism.

    The test is covering the auth mechanism.
    We could use any operation to test this, it should work the same as permanent AWS credentials.
    """
    client = aws_connector.get_aws_client(
        service="redshift",
        aws_config=get_test_aws_config_temporary_credentials(),
    )
    actual_result = aws_connector.describe_redshift_clusters(client=client)
    assert actual_result


@pytest.mark.external
def test_describe_rds_instances(tmpdir: LocalPath, test_config: FidesConfig) -> None:
    client = aws_connector.get_aws_client(
        service="rds",
        aws_config=get_test_aws_config(),
    )
    actual_result = aws_connector.describe_rds_instances(client=client)
    assert actual_result


@pytest.mark.external
def test_describe_rds_clusters(tmpdir: LocalPath, test_config: FidesConfig) -> None:
    client = aws_connector.get_aws_client(
        service="rds",
        aws_config=get_test_aws_config(),
    )
    actual_result = aws_connector.describe_rds_clusters(client=client)
    assert actual_result
