"""Module that adds functionality for generating or scanning systems."""
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from fideslang import manifests
from fideslang.models import Organization, System
from pydantic import AnyHttpUrl

from fidesctl.cli.utils import handle_cli_response
from fidesctl.connectors.models import AWSConfig
from fidesctl.core import api
from fidesctl.core.api_helpers import get_server_resource, get_server_resources
from fidesctl.core.parse import parse

from .filters import filter_aws_systems
from .utils import echo_green, echo_red


def generate_redshift_systems(
    organization_key: str, aws_config: Optional[AWSConfig]
) -> List[System]:
    """
    Fetches Redshift clusters from AWS and returns the transformed Sytem representations.
    """
    import fidesctl.connectors.aws as aws_connector

    client = aws_connector.get_aws_client(service="redshift", aws_config=aws_config)
    describe_clusters = aws_connector.describe_redshift_clusters(client=client)
    redshift_systems = aws_connector.create_redshift_systems(
        describe_clusters=describe_clusters, organization_key=organization_key
    )
    return redshift_systems


def generate_rds_systems(
    organization_key: str, aws_config: Optional[AWSConfig]
) -> List[System]:
    """
    Fetches RDS clusters and instances from AWS and returns the transformed Sytem representations.
    """
    import fidesctl.connectors.aws as aws_connector

    client = aws_connector.get_aws_client(service="rds", aws_config=aws_config)
    describe_clusters = aws_connector.describe_rds_clusters(client=client)
    describe_instances = aws_connector.describe_rds_instances(client=client)
    rds_systems = aws_connector.create_rds_systems(
        describe_clusters=describe_clusters,
        describe_instances=describe_instances,
        organization_key=organization_key,
    )
    return rds_systems


def get_organization(
    organization_key: str,
    manifest_organizations: List[Organization],
    url: AnyHttpUrl,
    headers: Dict[str, str],
) -> Optional[Organization]:
    """
    Attempts to find a given organization by key. Prioritizing a manifest organization
    list and then the server. Raises an error if it cannot find the organization.
    """
    taxonomy_organization = next(
        (org for org in manifest_organizations if org.fides_key == organization_key),
        None,
    )

    if taxonomy_organization:
        return taxonomy_organization

    server_organization = get_server_resource(
        url=url,
        resource_type="organization",
        resource_key=organization_key,
        headers=headers,
    )

    if not server_organization:
        echo_red(
            "Could not find organization ({}) to execute command".format(
                organization_key
            )
        )
        raise SystemExit(1)
    return server_organization


def generate_aws_systems(
    organization: Organization, aws_config: Optional[AWSConfig]
) -> List[System]:
    """
    Calls each generate system function for aws resources

    Returns a list of systems with any filters applied
    """
    generate_system_functions = [generate_redshift_systems, generate_rds_systems]

    aws_systems = [
        found_system
        for generate_function in generate_system_functions
        for found_system in generate_function(organization.fides_key, aws_config)
    ]

    filtered_aws_systems = filter_aws_systems(
        systems=aws_systems, organization=organization
    )
    return filtered_aws_systems


def generate_system_aws(
    file_name: str,
    include_null: bool,
    organization_key: str,
    aws_config: Optional[AWSConfig],
    url: AnyHttpUrl,
    headers: Dict[str, str],
) -> str:
    """
    Connect to an aws account by leveraging a valid boto3 environment varible
    configuration and extract tracked resource to write a System manifest with.
    Tracked resources: [Redshift, RDS]
    """
    _check_aws_connector_import()

    organization = get_organization(
        organization_key=organization_key,
        manifest_organizations=[],
        url=url,
        headers=headers,
    )
    aws_systems = generate_aws_systems(organization, aws_config=aws_config)

    output_list_of_dicts = [i.dict(exclude_none=not include_null) for i in aws_systems]
    manifests.write_manifest(
        file_name,
        output_list_of_dicts,
        "system",
    )
    echo_green(f"Generated system manifest written to {file_name}")
    return file_name


def get_system_arns(systems: List[System]) -> List[str]:
    """
    Given a list of systems, build a list of AWS ARNs
    """
    system_arns = [
        system.fidesctl_meta.resource_id
        for system in systems
        if system.fidesctl_meta and system.fidesctl_meta.resource_id
    ]
    return system_arns


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


def get_scan_resource_label(system_type: str) -> str:
    """
    Given a system type, returns the label to use in scan output
    """
    resource_label_map = {
        "redshift_cluster": "Redshift Cluster",
        "rds_instance": "RDS Instance",
        "rds_cluster": "RDS Cluster",
    }
    resource_label = resource_label_map.get(system_type, "Unknown")
    return resource_label


def scan_aws_systems(
    aws_systems: List[System],
    existing_system_arns: List[str],
) -> Tuple[str, int, int]:
    """
    Given a list of aws systems, compares resource arns to existing
    system arns. Returns missing resource text output, scanned
    resource count, and missing resource count.
    """
    aws_systems_by_type = defaultdict(list)
    for aws_system in aws_systems:
        aws_systems_by_type[aws_system.system_type].append(aws_system)

    scan_text_output = ""
    scanned_resource_count = 0
    missing_resource_count = 0
    for typed_aws_systems in aws_systems_by_type.values():
        resource_arns = get_system_arns(systems=typed_aws_systems)
        missing_resources = set(resource_arns) - set(existing_system_arns)
        scanned_resource_count += len(resource_arns)
        missing_resource_count += len(missing_resources)
        if missing_resource_count > 0:
            resource_label = get_scan_resource_label(
                system_type=typed_aws_systems[0].system_type
            )
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
    organization_key: str,
    aws_config: Optional[AWSConfig],
    coverage_threshold: int,
    url: AnyHttpUrl,
    headers: Dict[str, str],
) -> None:
    """
    Connect to an aws account by leveraging a valid boto3 environment varible
    configuration and compares tracked resources to existing systems.
    Tracked resources: [Redshift, RDS]
    """

    _check_aws_connector_import()

    manifest_taxonomy = parse(manifest_dir) if manifest_dir else None
    manifest_systems = manifest_taxonomy.system if manifest_taxonomy else []
    server_systems = get_all_server_systems(
        url=url, headers=headers, exclude_systems=manifest_systems
    )
    existing_system_arns = get_system_arns(systems=manifest_systems + server_systems)

    organization = get_organization(
        organization_key=organization_key,
        manifest_organizations=manifest_taxonomy.organization
        if manifest_taxonomy
        else [],
        url=url,
        headers=headers,
    )

    aws_systems = generate_aws_systems(organization=organization, aws_config=aws_config)

    (
        scan_text_output,
        scanned_resource_count,
        missing_resource_count,
    ) = scan_aws_systems(
        aws_systems=aws_systems,
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


def _check_aws_connector_import() -> None:
    "Validates boto3 is installed and can be imported"
    try:
        import fidesctl.connectors.aws  # pylint: disable=unused-import
    except ModuleNotFoundError:
        echo_red('Packages not found, try: pip install "fidesctl[aws]"')
        raise SystemExit
