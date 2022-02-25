"""Module that adds functionality for generating or scanning systems."""
from typing import Dict, List, Tuple, Callable

import boto3

from pydantic import AnyHttpUrl

from fidesctl.cli.utils import handle_cli_response
from fidesctl.core import api
from fidesctl.core.parse import parse
from fidesctl.core.api_helpers import get_server_resources
from fideslang import manifests
from fideslang.models import System, SystemMetadata

from .utils import echo_green, echo_red


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


def get_redshift_arns(describe_clusters: Dict[str, List[Dict]]) -> List[str]:
    """
    Given a describe clusters response, build a list of cluster arns
    """
    redshift_arns = [
        cluster["ClusterNamespaceArn"] for cluster in describe_clusters["Clusters"]
    ]
    return redshift_arns


def scan_redshift_systems() -> Tuple[str, List[str]]:
    """
    Fetches Redshift clusters from AWS and returns a scan label and
    list of cluster arns.
    """
    redshift_clusters = describe_redshift_clusters()
    redshift_arns = get_redshift_arns(describe_clusters=redshift_clusters)
    return "Redshift Clusters", redshift_arns


def get_all_server_systems(
    url: AnyHttpUrl, headers: Dict[str, str], exclude_systems: List[System]
) -> List[System]:
    """
    Get a list of all of the Systems that exist on the server. Excludes any systems
    provided in exclude_systems
    """
    ls_response = handle_cli_response(
        api.ls(url=url, resource_type="system", headers=headers), verbose=False
    )
    exclude_system_keys = [system.fides_key for system in exclude_systems]
    system_keys = [
        resource["fides_key"]
        for resource in ls_response.json()
        if resource["fides_key"] not in exclude_system_keys
    ]
    system_list = get_server_resources(
        url=url, resource_type="system", headers=headers, existing_keys=system_keys
    )
    return system_list


def scan_aws_systems(
    scan_system_functions: List[Callable[[], Tuple[str, List[str]]]],
    existing_system_arns: List[str],
) -> Tuple[str, int, int]:
    """
    Given a list of scan system functions, compares function result to
    existing system arns. Returns missing resource text output, scanned
    resource count, and missing resource count.
    """
    scan_text_output = ""
    scanned_resource_count = 0
    missing_resource_count = 0
    for scan_system_function in scan_system_functions:
        resource_label, resource_arns = scan_system_function()
        missing_resources = set(resource_arns) - set(existing_system_arns)
        scanned_resource_count += len(resource_arns)
        missing_resource_count += len(missing_resources)
        if missing_resource_count > 0:
            scan_text_output += f"Missing {resource_label}:\n"
            scan_text_output += "\t{}\n".format("\n\t".join(missing_resources))

    return scan_text_output, scanned_resource_count, missing_resource_count


def print_scan_system_aws_result(
    scan_text_output: str,
    scanned_resource_count: int,
    missing_resource_count: int,
    coverage_threshold: int,
) -> None:
    """
    Prints uncategorized fields and raises an exception if coverage
    is lower than provided threshold.
    """
    if missing_resource_count < 1:
        echo_green(
            f"Scanned {scanned_resource_count} resources and all were found in taxonomy."
        )
    else:
        echo_red(
            f"Scanned {scanned_resource_count} resource(s) and found {missing_resource_count} missing resource(s).\n"
            + scan_text_output
        )

    coverage_percent = int(
        ((scanned_resource_count - missing_resource_count) / scanned_resource_count)
        * 100
    )
    annotation_output = "Resource coverage: {}%".format(coverage_percent)
    if coverage_percent < coverage_threshold:
        echo_red(annotation_output)
        raise SystemExit(1)
    echo_green(annotation_output)


def scan_system_aws(
    manifest_dir: str,
    coverage_threshold: int,
    url: AnyHttpUrl,
    headers: Dict[str, str],
) -> None:
    """
    Connect to an aws account by leveraging a valid boto3 environment varible
    configuration and compares tracked resources to existing systems.
    Tracked resources: [Redshift]
    """
    scan_system_functions = [scan_redshift_systems]

    manifest_taxonomy = parse(manifest_dir) if manifest_dir else None
    manifest_systems = manifest_taxonomy.system if manifest_taxonomy else []
    server_systems = get_all_server_systems(
        url=url, headers=headers, exclude_systems=manifest_systems
    )
    existing_system_arns = [
        system.fidesctl_meta.resource_id
        for system in manifest_systems + server_systems
        if system.fidesctl_meta and system.fidesctl_meta.resource_id
    ]

    (
        scan_text_output,
        scanned_resource_count,
        missing_resource_count,
    ) = scan_aws_systems(
        scan_system_functions=scan_system_functions,
        existing_system_arns=existing_system_arns,
    )

    if scanned_resource_count < 1:
        echo_red("Did not find any resources to scan in AWS account")
        raise SystemExit(1)

    print_scan_system_aws_result(
        scan_text_output=scan_text_output,
        scanned_resource_count=scanned_resource_count,
        missing_resource_count=missing_resource_count,
        coverage_threshold=coverage_threshold,
    )
