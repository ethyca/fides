"""Module that adds interactions with aws"""
from typing import Any, Dict, List, Optional

import boto3
from fideslang.models import System, SystemMetadata

from fidesctl.connectors.models import AWSConfig


def get_aws_client(service: str, aws_config: Optional[AWSConfig]) -> Any:  # type: ignore
    """
    Creates boto3 redshift client and returns describe_clusters response.
    """
    config_dict = aws_config.dict() if aws_config else {}
    service_client = boto3.client(
        service,
        **config_dict,
    )
    return service_client


def describe_redshift_clusters(client: Any) -> Dict[str, List[Dict]]:  # type: ignore
    """
    Creates boto3 redshift client and returns describe_clusters response.
    """
    describe_clusters = client.describe_clusters()
    return describe_clusters


def describe_rds_clusters(client: Any) -> Dict[str, List[Dict]]:  # type: ignore
    """
    Creates boto3 rds client and returns describe_db_clusters response.
    """
    describe_clusters = client.describe_db_clusters()
    return describe_clusters


def describe_rds_instances(client: Any) -> Dict[str, List[Dict]]:  # type: ignore
    """
    Creates boto3 rds client and returns describe_db_instances response.
    """
    describe_instances = client.describe_db_instances()
    return describe_instances


def create_redshift_systems(
    describe_clusters: Dict[str, List[Dict]], organization_key: str
) -> List[System]:
    """
    Given a "describe_clusters" response, build a system object which represents
    each cluster.
    """
    redshift_systems = [
        System(
            fides_key=cluster["ClusterIdentifier"],
            name=cluster["ClusterIdentifier"],
            description=f"Fides Generated Description for Redshift Cluster: {cluster['ClusterIdentifier']}",
            system_type="redshift_cluster",
            organization_fides_key=organization_key,
            fidesctl_meta=SystemMetadata(
                endpoint_address=cluster["Endpoint"]["Address"]
                if cluster.get("Endpoint")
                else None,
                endpoint_port=cluster["Endpoint"]["Port"]
                if cluster.get("Endpoint")
                else None,
                resource_id=cluster["ClusterNamespaceArn"],
            ),
            privacy_declarations=[],
        )
        for cluster in describe_clusters["Clusters"]
    ]
    return redshift_systems


def create_rds_systems(
    describe_clusters: Dict[str, List[Dict]],
    describe_instances: Dict[str, List[Dict]],
    organization_key: str,
) -> List[System]:
    """
    Given "describe_clusters" and "describe_instances" responses, build a system object
    which represents each cluster or instance.

    A system is created for each cluster, but for instances we only create a system if
    it is not part of a cluster
    """
    rds_cluster_systems = [
        System(
            fides_key=cluster["DBClusterIdentifier"],
            name=cluster["DBClusterIdentifier"],
            description=f"Fides Generated Description for RDS Cluster: {cluster['DBClusterIdentifier']}",
            system_type="rds_cluster",
            organization_fides_key=organization_key,
            fidesctl_meta=SystemMetadata(
                endpoint_address=cluster["Endpoint"],
                endpoint_port=cluster["Port"],
                resource_id=cluster["DBClusterArn"],
            ),
            privacy_declarations=[],
        )
        for cluster in describe_clusters["DBClusters"]
    ]
    rds_instances_systems = [
        System(
            fides_key=instance["DBInstanceIdentifier"],
            name=instance["DBInstanceIdentifier"],
            description=f"Fides Generated Description for RDS Instance: {instance['DBInstanceIdentifier']}",
            system_type="rds_instance",
            organization_fides_key=organization_key,
            fidesctl_meta=SystemMetadata(
                endpoint_address=instance["Endpoint"]["Address"]
                if instance.get("Endpoint")
                else None,
                endpoint_port=instance["Endpoint"]["Port"]
                if instance.get("Endpoint")
                else None,
                resource_id=instance["DBInstanceArn"],
            ),
            privacy_declarations=[],
        )
        for instance in describe_instances["DBInstances"]
        if not instance.get("DBClusterIdentifier")
    ]
    return rds_cluster_systems + rds_instances_systems
