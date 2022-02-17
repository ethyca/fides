"""Module that adds functionality for generating or scanning systems."""
from typing import Dict, List

import boto3

from fideslang import manifests
from fideslang.models import System, SystemMetadata
from .utils import echo_green


def describe_redshift_clusters() -> Dict[str, List[Dict]]:
    """
    Creates boto3 redshift client and returns describe_clusters response.
    """
    redshift_client = boto3.client(
        "redshift",
    )
    describe_clusters = redshift_client.describe_clusters()
    return describe_clusters


def transform_redshift_systems(
    describe_clusters: Dict[str, List[Dict]]
) -> List[System]:
    """
    Given a describe clusters response, build a system object which represents
    each cluster.
    """
    redshift_systems = [
        System(
            fides_key=cluster["ClusterIdentifier"],
            name=cluster["ClusterIdentifier"],
            description=f"Fides Generated Description for Cluster: {cluster['ClusterIdentifier']}",
            system_type="redshift_cluster",
            fidesctl_meta=SystemMetadata(
                endpoint_address=cluster["Endpoint"]["Address"]
                if cluster["Endpoint"]
                else None,
                endpoint_port=cluster["Endpoint"]["Port"]
                if cluster["Endpoint"]
                else None,
                resource_id=cluster["ClusterNamespaceArn"],
            ),
            privacy_declarations=[],
        )
        for cluster in describe_clusters["Clusters"]
    ]
    return redshift_systems


def generate_redshift_systems() -> List[System]:
    """
    Fetches Redshift clusters from AWS and returns the transformed Sytem representations.
    """
    describe_clusters = describe_redshift_clusters()
    redshift_systems = transform_redshift_systems(describe_clusters=describe_clusters)
    return redshift_systems


def generate_system_aws(file_name: str, include_null: bool) -> str:
    """
    Connect to an aws account by leveraging a valid boto3 environment varible
    configuration and extract tracked resource to write a System manifest with.
    Tracked resources: [Redshift]
    """
    generate_system_functions = [generate_redshift_systems]
    aws_systems = [
        found_system
        for generate_function in generate_system_functions
        for found_system in generate_function()
    ]
    manifests.write_manifest(
        file_name,
        [i.dict(exclude_none=not include_null) for i in aws_systems],
        "system",
    )
    echo_green(f"Generated system manifest written to {file_name}")
    return file_name
