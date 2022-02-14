"""Module that adds functionality for generating or scanning systems."""
from typing import Dict, List

import boto3

from fideslang import manifests
from fideslang.models import System
from .utils import echo_green


def create_redshift_systems(describe_clusters: Dict[str, List[Dict]]) -> List[System]:
    """
    Given a describe clusters response,build a system object which represents
    each cluster
    """
    redshift_systems = [
        System(
            fides_key=cluster["ClusterIdentifier"],
            name=cluster["ClusterIdentifier"],
            description=f"Fides Generated Description for Cluster: {cluster['ClusterIdentifier']}",
            system_type="redshift_cluster",
            system_resource_id=cluster["ClusterNamespaceArn"],
            meta={
                "endpoint_address": cluster["Endpoint"]["Address"],
                "endpoint_port": cluster["Endpoint"]["Port"],
            },
            privacy_declarations=[],
        )
        for cluster in describe_clusters["Clusters"]
    ]
    return redshift_systems


def generate_system_aws(file_name: str, include_null: bool) -> str:
    """
    Connect to an aws account by leveraging a valid boto3 environment varible
    configuration and extract tracked resource to write a System manifest with.
    Tracked resources: [Redshift]
    """
    redshift_client = boto3.client(
        "redshift",
    )
    describe_redshift_clusters = redshift_client.describe_clusters()
    redshift_systems = create_redshift_systems(
        describe_clusters=describe_redshift_clusters
    )

    print(describe_redshift_clusters)
    print(redshift_systems)
    manifests.write_manifest(
        file_name,
        [i.dict(exclude_none=not include_null) for i in redshift_systems],
        "system",
    )
    echo_green(f"Generated dataset manifest written to {file_name}")
    return file_name
