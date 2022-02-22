import pytest

from fidesctl.core import system as _system
from fideslang.models import System, SystemMetadata


@pytest.mark.unit
def test_transform_redshift_systems():
    describe_clusters = {
        "Clusters": [
            {
                "ClusterIdentifier": "redshift-cluster-1",
                "Endpoint": {
                    "Address": "redshift-cluster-1.c2angfh5kpo4.us-east-1.redshift.amazonaws.com",
                    "Port": 5439,
                },
                "ClusterNamespaceArn": "arn:aws:redshift:us-east-1:910934740016:namespace:057d5b0e-7eaa-4012-909c-3957c7149176",
            }
        ]
    }
    expected_result = [
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
        )
    ]
    actual_result = _system.transform_redshift_systems(describe_clusters)
    assert actual_result == expected_result


@pytest.mark.external
def test_generate_system_aws(tmpdir):
    actual_result = _system.generate_system_aws(f"{tmpdir}/test_file.yml", False)
    assert actual_result
