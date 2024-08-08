"""Module that adds functionality for generating or scanning systems."""

import asyncio
from collections import defaultdict
from typing import Dict, List, Optional

from fideslang import manifests
from fideslang.models import Organization, System
from fideslang.validation import AnyHttpUrlString

from fides.common.utils import echo_green, echo_red, handle_cli_response
from fides.connectors.models import AWSConfig, OktaConfig
from fides.core import api
from fides.core.api_helpers import get_server_resource, get_server_resources
from fides.core.filters import filter_aws_systems
from fides.core.parse import parse


def generate_redshift_systems(
    organization_key: str, aws_config: Optional[AWSConfig]
) -> List[System]:
    """
    Fetches Redshift clusters from AWS and returns the transformed System representations.
    """
    import fides.connectors.aws as aws_connector

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
    Fetches RDS clusters and instances from AWS and returns the transformed System representations.
    """
    import fides.connectors.aws as aws_connector

    client = aws_connector.get_aws_client(service="rds", aws_config=aws_config)
    describe_clusters = aws_connector.describe_rds_clusters(client=client)
    describe_instances = aws_connector.describe_rds_instances(client=client)
    rds_systems = aws_connector.create_rds_systems(
        describe_clusters=describe_clusters,
        describe_instances=describe_instances,
        organization_key=organization_key,
    )
    return rds_systems


def generate_resource_tagging_systems(
    organization_key: str, aws_config: Optional[AWSConfig]
) -> List[System]:
    """
    Fetches AWS Resources from the resource tagging api and returns the transformed System representations.
    """
    import fides.connectors.aws as aws_connector

    client = aws_connector.get_aws_client(
        service="resourcegroupstaggingapi", aws_config=aws_config
    )
    resources = aws_connector.get_tagging_resources(client=client)
    resource_tagging_systems = aws_connector.create_resource_tagging_systems(
        resources=resources, organization_key=organization_key
    )
    return resource_tagging_systems


def get_organization(
    organization_key: str,
    manifest_organizations: List[Organization],
    url: AnyHttpUrlString,
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
        url=str(url),
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

    parsed_organization = Organization.model_validate(server_organization)
    assert isinstance(parsed_organization, Organization)
    return parsed_organization


def generate_aws_systems(
    organization: Organization, aws_config: Optional[AWSConfig]
) -> List[System]:
    """
    Calls each generate system function for aws resources

    Returns a list of systems with any filters applied
    """
    generate_system_functions = [
        generate_redshift_systems,
        generate_rds_systems,
        generate_resource_tagging_systems,
    ]

    aws_systems = [
        found_system
        for generate_function in generate_system_functions
        for found_system in generate_function(organization.fides_key, aws_config)
    ]

    filtered_aws_systems = filter_aws_systems(
        systems=aws_systems, organization=organization
    )
    return filtered_aws_systems


def write_system_manifest(
    file_name: str, include_null: bool, systems: List[System]
) -> None:
    """
    Given a list of systems, writes a manifest file with the given systems.

    An optional flag can be passed to include null fields.
    """
    manifests.write_manifest(
        file_name,
        [i.model_dump(exclude_none=not include_null) for i in systems],
        "system",
    )
    echo_green(f"Generated system manifest written to {file_name}")


def generate_system_aws(
    file_name: str,
    include_null: bool,
    organization_key: str,
    aws_config: Optional[AWSConfig],
    url: AnyHttpUrlString,
    headers: Dict[str, str],
) -> str:
    """
    Connect to an aws account by leveraging a valid boto3 environment varible
    configuration and extract tracked resource to write a System manifest with.
    """

    organization = get_organization(
        organization_key=organization_key,
        manifest_organizations=[],
        url=url,
        headers=headers,
    )
    assert organization
    aws_systems = generate_aws_systems(organization, aws_config=aws_config)

    write_system_manifest(
        file_name=file_name, include_null=include_null, systems=aws_systems
    )
    return file_name


async def generate_okta_systems(
    organization: Organization, okta_config: Optional[OktaConfig]
) -> List[System]:
    """
    Given an okta configuration, calls okta for a list of
    applications and returns the corresponding systems.
    """

    import fides.connectors.okta as okta_connector

    okta_client = okta_connector.get_okta_client(okta_config)
    okta_applications = await okta_connector.list_okta_applications(
        okta_client=okta_client
    )
    okta_systems = okta_connector.create_okta_systems(
        okta_applications=okta_applications, organization_key=organization.fides_key
    )
    return okta_systems


def generate_system_okta(
    organization_key: str,
    okta_config: Optional[OktaConfig],
    file_name: str,
    include_null: bool,
    url: AnyHttpUrlString,
    headers: Dict[str, str],
) -> str:
    """
    Generates a system manifest from existing Okta applications.
    """

    organization = get_organization(
        organization_key=organization_key,
        manifest_organizations=[],
        url=url,
        headers=headers,
    )
    assert organization

    okta_systems = asyncio.run(
        generate_okta_systems(organization=organization, okta_config=okta_config)
    )

    write_system_manifest(
        file_name=file_name, include_null=include_null, systems=okta_systems
    )
    return file_name


def get_all_server_systems(
    url: AnyHttpUrlString, headers: Dict[str, str], exclude_systems: List[System]
) -> List[System]:
    """
    Get a list of all of the Systems that exist on the server. Excludes any systems
    provided in exclude_systems
    """
    ls_response = handle_cli_response(
        api.ls(url=str(url), resource_type="system", headers=headers), verbose=False
    )
    exclude_system_keys = [system.fides_key for system in exclude_systems]
    system_keys = [
        resource["fides_key"]
        for resource in ls_response.json()
        if resource["fides_key"] not in exclude_system_keys
    ]

    # The validation here is required to guarantee the return type
    system_list = [
        System.validate(x)
        for x in get_server_resources(
            url=str(url),
            resource_type="system",
            headers=headers,
            existing_keys=system_keys,
        )
    ]

    return system_list


def get_scan_resource_label(system_type: str) -> str:
    """
    Given a system type, returns the label to use in scan output
    """
    resource_label_map = {
        "redshift_cluster": "Redshift Cluster",
        "rds_instance": "RDS Instance",
        "rds_cluster": "RDS Cluster",
        "okta_application": "Okta Application",
    }
    resource_label = resource_label_map.get(system_type, "Unknown")
    return resource_label


def get_system_resource_ids(systems: List[System]) -> List[str]:
    """
    Given a list of systems, build a list of resource ids
    """
    system_resource_ids = []
    for system in systems:
        resource_id = get_system_resource_id(system=system)
        if resource_id:
            system_resource_ids.append(resource_id)
    return system_resource_ids


def get_system_resource_id(system: System) -> Optional[str]:
    """
    Given a resource system, returns the resource id. Returns None
    if a resource_id is not found in metadata.
    """
    system_resource_id = (
        system.fidesctl_meta.resource_id
        if system.fidesctl_meta and system.fidesctl_meta.resource_id
        else None
    )
    return system_resource_id


def find_missing_systems(
    source_systems: List[System],
    existing_systems: List[System],
) -> List[System]:
    """
    Given a list of source and existing systems, returns a list
    of systems which are not found in the existing list.
    """
    existing_resource_ids = get_system_resource_ids(systems=existing_systems)
    missing_systems = [
        source_system
        for source_system in source_systems
        if get_system_resource_id(system=source_system) not in existing_resource_ids
    ]
    return missing_systems


def print_system_resource_scan_result(
    source_systems: List[System],
    missing_systems: List[System],
    coverage_threshold: int,
) -> None:
    """
    Prints missing systems and raises an exception if coverage
    is lower than provided threshold.
    """
    output: str = "Successfully scanned the following systems:\n"
    for source_system in source_systems:
        output += "\t{}(id={})\n".format(
            source_system.name, get_system_resource_id(system=source_system)
        )
    echo_green(output)

    if missing_systems:
        missing_systems_output = (
            "The following system were not found in existing manifest\n"
        )

        # first group the systems by type to print them grouped
        missing_systems_by_type = defaultdict(list)
        for missing_system in missing_systems:
            missing_systems_by_type[missing_system.system_type].append(missing_system)

        for typed_missing_systems in missing_systems_by_type.values():
            resource_label = get_scan_resource_label(
                system_type=typed_missing_systems[0].system_type
            )
            missing_systems_output += f"Missing {resource_label}:\n"

            for typed_missing_system in typed_missing_systems:
                missing_systems_output += "\t{}(id={})\n".format(
                    typed_missing_system.name,
                    get_system_resource_id(system=typed_missing_system),
                )
        echo_red(missing_systems_output)

    coverage_percent = int(
        ((len(source_systems) - len(missing_systems)) / len(source_systems)) * 100
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
    url: AnyHttpUrlString,
    headers: Dict[str, str],
) -> None:
    """
    Connect to an aws account by leveraging a valid boto3 environment varible
    configuration and compares tracked resources to existing systems.
    """

    manifest_taxonomy = parse(manifest_dir) if manifest_dir else None
    manifest_systems = (
        manifest_taxonomy.system
        if manifest_taxonomy and manifest_taxonomy.system
        else []
    )
    server_systems = get_all_server_systems(
        url=url, headers=headers, exclude_systems=manifest_systems
    )
    existing_systems = manifest_systems + server_systems

    organization = get_organization(
        organization_key=organization_key,
        manifest_organizations=(
            manifest_taxonomy.organization if manifest_taxonomy else []
        ),
        url=url,
        headers=headers,
    )
    assert organization

    aws_systems = generate_aws_systems(organization=organization, aws_config=aws_config)

    if len(aws_systems) < 1:
        echo_red("AWS did not return any resources to scan systems")
        raise SystemExit(1)

    missing_systems = find_missing_systems(
        source_systems=aws_systems,
        existing_systems=existing_systems,
    )
    print_system_resource_scan_result(
        source_systems=aws_systems,
        missing_systems=missing_systems,
        coverage_threshold=coverage_threshold,
    )


def scan_system_okta(
    manifest_dir: str,
    organization_key: str,
    okta_config: Optional[OktaConfig],
    coverage_threshold: int,
    url: AnyHttpUrlString,
    headers: Dict[str, str],
) -> None:
    """
    Fetches Okta applications and compares them against existing
    systems in the server and manifest supplied.
    """

    manifest_taxonomy = parse(manifest_dir) if manifest_dir else None
    manifest_systems = (
        manifest_taxonomy.system
        if manifest_taxonomy and manifest_taxonomy.system
        else []
    )
    server_systems = get_all_server_systems(
        url=url, headers=headers, exclude_systems=manifest_systems
    )

    organization = get_organization(
        organization_key=organization_key,
        manifest_organizations=(
            manifest_taxonomy.organization if manifest_taxonomy else []
        ),
        url=url,
        headers=headers,
    )
    assert organization

    okta_systems = asyncio.run(
        generate_okta_systems(organization=organization, okta_config=okta_config)
    )

    if len(okta_systems) < 1:
        echo_red("Okta did not return any applications to scan systems")
        raise SystemExit(1)

    missing_systems = find_missing_systems(
        source_systems=okta_systems,
        existing_systems=server_systems + manifest_systems,
    )
    print_system_resource_scan_result(
        source_systems=okta_systems,
        missing_systems=missing_systems,
        coverage_threshold=coverage_threshold,
    )
