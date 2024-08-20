"""Module that adds interactions with aws"""

from functools import update_wrapper
from typing import Any, Callable, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError
from fideslang.models import (
    Dataset,
    DatasetCollection,
    DatasetField,
    System,
    SystemMetadata,
)
from loguru import logger

from fides.connectors.models import (
    AWSConfig,
    ConnectorAuthFailureException,
    ConnectorFailureException,
)
from fides.core.utils import generate_unique_fides_key


def get_aws_client(service: str, aws_config: Optional[AWSConfig]) -> Any:
    """
    Creates boto3 client for a given service. A config is optional
    to allow for environment variable configuration.
    """
    config_dict = aws_config.model_dump(mode="json") if aws_config else {}
    service_client = boto3.client(
        service,
        **config_dict,
    )  # type: ignore
    return service_client


def handle_common_aws_errors(func: Callable) -> Callable:
    """
    Function decorator which handles common errors for aws calls.
    Classifies exceptions based on error codes returned by the client.
    """

    def wrapper_func(*args, **kwargs) -> Any:  # type: ignore
        try:
            return func(*args, **kwargs)
        except ClientError as error:
            logger.warning(error.response["Error"]["Code"])
            if error.response["Error"]["Code"] in [
                "InvalidClientTokenId",
                "SignatureDoesNotMatch",
            ]:
                raise ConnectorAuthFailureException(error.response["Error"]["Message"])
            if error.response["Error"]["Code"] in [
                "AccessDenied",
                "AccessDeniedException",
            ]:
                logger.warning(error.response["Error"]["Message"])
                return []
            raise ConnectorFailureException(error.response["Error"]["Message"])

    return update_wrapper(wrapper_func, func)


@handle_common_aws_errors
def validate_credentials(aws_config: Optional[AWSConfig]) -> None:
    """
    Calls the get_caller_identity sts api to validate aws credentials
    """
    client = get_aws_client("sts", aws_config)
    client.get_caller_identity()


@handle_common_aws_errors
def describe_redshift_clusters(client: Any) -> Dict[str, List[Dict]]:  # type: ignore
    """
    Returns describe_clusters response given a 'redshift' boto3 client.
    """
    describe_clusters = client.describe_clusters()
    return describe_clusters


@handle_common_aws_errors
def describe_rds_clusters(client: Any) -> Dict[str, List[Dict]]:  # type: ignore
    """
    Returns describe_db_clusters response given a rds boto3 client.
    """
    describe_clusters = client.describe_db_clusters()
    return describe_clusters


@handle_common_aws_errors
def describe_rds_instances(client: Any) -> Dict[str, List[Dict]]:  # type: ignore
    """
    Returns describe_db_instances response given a 'rds' boto3 client.
    """
    describe_instances = client.describe_db_instances()
    return describe_instances


@handle_common_aws_errors
def describe_dynamo_tables(client: Any, table_names: List[str]) -> List[Dict]:  # type: ignore
    """
    Returns describe_table response given a 'dynamodb' boto3 client.
    """
    describe_tables = []
    for table_name in table_names:
        described_table = describe_dynamo_table(client, table_name)
        if isinstance(described_table, dict):
            describe_tables.append(described_table)

    return describe_tables


@handle_common_aws_errors
def describe_dynamo_table(client: Any, table_name: str) -> Dict:  # type: ignore
    """
    Returns describe_table response given a 'dynamodb' boto3 client.
    """
    described_table = client.describe_table(TableName=table_name)
    described_table["Table"]["Fields"] = scan_dynamo_table(client, table_name)

    return described_table["Table"]


@handle_common_aws_errors
def get_dynamo_tables(client: Any) -> List[str]:  # type: ignore
    """
    Returns a list of table names response given a 'rds' boto3 client.
    """
    list_tables = client.list_tables()
    table_names = list_tables["TableNames"]
    next_page_exists = "LastEvaluatedTableName" in list_tables
    while next_page_exists:
        last_evaluated_table_name = list_tables["LastEvaluatedTableName"]
        list_tables = client.list_tables(
            ExclusiveStartTableName=last_evaluated_table_name
        )
        table_names.extend(list_tables["TableNames"])
        next_page_exists = "LastEvaluatedTableName" in list_tables
    return table_names


@handle_common_aws_errors
def scan_dynamo_table(client: Any, table_name: str, num_samples: int = 30) -> List[str]:  # type: ignore
    """
    Returns describe_table response given a 'dynamodb' boto3 client.
    """
    table_scan = client.scan(TableName=table_name, Limit=num_samples)
    fields = set()
    for item in table_scan["Items"]:
        for field, _ in item.items():
            fields.add(field)

    return list(fields)


@handle_common_aws_errors
def get_tagging_resources(client: Any) -> List[Dict]:  # type: ignore
    """
    Returns a list of resources given a 'resourcegroupstaggingapi' boto3 client.
    """
    paginator = client.get_paginator("get_resources")
    resources = [
        resource
        for page in paginator.paginate()
        for resource in page["ResourceTagMappingList"]
    ]
    return resources


def create_dynamodb_dataset(
    described_dynamo_tables: List[Dict],
    organization_key: str = "default_organization",
    single_dataset: bool = False,
) -> List[Dataset]:
    """
    Given "describe_table" response(s), build a dataset object to represent
    each dynamodb table, returning a fides dataset.
    """
    # TODO: add something for improved dataset uniqueness, i.e. region/account
    if single_dataset:
        dataset_name = "DynamoDB"
        unique_dataset_name = generate_unique_fides_key(dataset_name, "", "")
        datasets = [
            Dataset(
                name=dataset_name,
                fides_key=unique_dataset_name,
                organization_fides_key=organization_key,
                collections=[
                    DatasetCollection(
                        name=collection["TableName"],
                        # description=collection["TableArn"],
                        fields=[
                            DatasetField(
                                name=field,
                                description=f"Fides Generated Description for Column: {field}",
                                data_categories=[],
                                # TODO: include a fieldsmeta if the field is a primary key or secondary sort (and test for both)
                            )
                            for field in collection["Fields"]
                        ],
                    )
                    for collection in described_dynamo_tables
                ],
            )
        ]
    else:
        datasets = [
            Dataset(
                name=collection["TableName"],
                fides_key=generate_unique_fides_key(collection["TableName"], "", ""),
                organization_fides_key=organization_key,
                collections=[
                    DatasetCollection(
                        name=collection["TableName"],
                        # description=collection["TableArn"],
                        fields=[
                            DatasetField(
                                name=field,
                                description=f"Fides Generated Description for Column: {field}",
                                data_categories=[],
                                # TODO: include a fieldsmeta if the field is a primary key or secondary sort (and test for both)
                            )
                            for field in collection["Fields"]
                        ],
                    )
                ],
            )
            for collection in described_dynamo_tables
        ]
    return datasets


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
            meta={pair["Key"]: pair["Value"] for pair in cluster.get("Tags", {})},
            system_type="redshift_cluster",
            organization_fides_key=organization_key,
            fidesctl_meta=SystemMetadata(
                endpoint_address=(
                    cluster["Endpoint"]["Address"] if cluster.get("Endpoint") else None
                ),
                endpoint_port=(
                    cluster["Endpoint"]["Port"] if cluster.get("Endpoint") else None
                ),
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
            meta={pair["Key"]: pair["Value"] for pair in cluster.get("TagList", {})},
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
            meta={pair["Key"]: pair["Value"] for pair in instance.get("TagList", {})},
            system_type="rds_instance",
            organization_fides_key=organization_key,
            fidesctl_meta=SystemMetadata(
                endpoint_address=(
                    instance["Endpoint"]["Address"]
                    if instance.get("Endpoint")
                    else None
                ),
                endpoint_port=(
                    instance["Endpoint"]["Port"] if instance.get("Endpoint") else None
                ),
                resource_id=instance["DBInstanceArn"],
            ),
            privacy_declarations=[],
        )
        for instance in describe_instances["DBInstances"]
        if not instance.get("DBClusterIdentifier")
    ]
    return rds_cluster_systems + rds_instances_systems


def create_resource_tagging_systems(
    resources: List[Dict],
    organization_key: str,
) -> List[System]:
    """
    Given a list of resources, build a list of systems object which represents
    each resource.
    """
    resource_generators = {
        "dynamodb": create_tagging_dynamodb_system,
        "s3": create_tagging_s3_system,
    }
    systems = []
    for resource in resources:
        arn_split = resource["ResourceARN"].split(":")
        arn_resource_type = arn_split[2]
        resource_generator = resource_generators.get(arn_resource_type)
        if resource_generator:
            generated_system = resource_generator(resource, organization_key)
            if generated_system:
                systems.append(generated_system)
    return systems


def create_tagging_dynamodb_system(
    resource: Dict[str, Any], organization_key: str
) -> Optional[System]:
    """
    Given an AWS dynamodb resource, returns a System representation
    for dynamodb tables.
    """
    arn = resource["ResourceARN"]
    arn_split = arn.split(":")
    resource_name = arn_split[5]

    if resource_name.startswith("table/"):
        table_name = resource_name[len("table/") :]
        system = System(
            fides_key=table_name,
            name=table_name,
            description=f"Fides Generated Description for DynamoDb table: {table_name}",
            meta={pair["Key"]: pair["Value"] for pair in resource.get("Tags", {})},
            system_type="dynamodb_table",
            organization_fides_key=organization_key,
            fidesctl_meta=SystemMetadata(
                resource_id=arn,
            ),
            privacy_declarations=[],
        )
        return system
    return None


def create_tagging_s3_system(
    resource: Dict[str, Any], organization_key: str
) -> Optional[System]:
    """
    Given an AWS s3 resource, returns a System representation
    for s3 buckets.
    """
    arn = resource["ResourceARN"]
    arn_split = arn.split(":")
    resource_name = arn_split[5]

    bucket_name = resource_name.split("/")[0]
    system = System(
        fides_key=bucket_name,
        name=bucket_name,
        description=f"Fides Generated Description for S3 bucket: {bucket_name}",
        meta={pair["Key"]: pair["Value"] for pair in resource.get("Tags", {})},
        system_type="s3_bucket",
        organization_fides_key=organization_key,
        fidesctl_meta=SystemMetadata(
            resource_id=arn,
        ),
        privacy_declarations=[],
    )
    return system
