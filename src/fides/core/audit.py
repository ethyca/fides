from typing import Dict, List, Optional, Union

from fideslang.models import DataSubject, FidesModel, Organization, System
from fideslang.parse import parse_dict

from fides.common.utils import echo_green, echo_red, pretty_echo
from fides.core.api_helpers import (
    get_server_resource,
    get_server_resources,
    list_server_resources,
)


def audit_systems(
    url: str,
    headers: Dict[str, str],
    include_keys: Optional[List] = None,
) -> None:
    """
    Audits the system resources from the server for compliance.

    This should be flexible enough to accept further audits in
    the future and return them as well as being called from other
    audit functions.
    """
    # get the server resources for systems
    system_resources: Optional[Union[List[FidesModel], List[Dict]]]

    if include_keys:
        system_resources = get_server_resources(url, "system", include_keys, headers)
    else:
        system_resources = list_server_resources(
            url, headers, "system", exclude_keys=[]
        )

    if not system_resources:
        print("No system resources were found.")
        return

    print(f"Found {len(system_resources)} System resource(s) to audit...")
    audit_findings = 0
    for system in system_resources:
        pretty_echo(
            f"Auditing System: {system.name if isinstance(system, FidesModel) else system['name']}"
        )
        assert isinstance(system, System)
        new_findings = validate_system_attributes(system, url, headers)
        audit_findings = audit_findings + new_findings

    if audit_findings > 0:
        print(
            f"{audit_findings} issue(s) were detected in auditing system completeness."
        )
    else:
        echo_green("All audited system resource(s) compliant!")


def validate_system_attributes(
    system: System,
    url: str,
    headers: Dict[str, str],
) -> int:
    """
    Validates one or multiple attributes are set on a system
    """

    new_findings = 0
    if system.administrating_department == "Not defined":
        echo_red(
            f"{system.name} should have a responsible group, defined as 'administrating_department'."
        )
        new_findings += 1

    for privacy_declaration in system.privacy_declarations:
        for data_subject_fides_key in privacy_declaration.data_subjects:
            raw_data_subject = get_server_resource(
                url, "data_subject", data_subject_fides_key, headers
            )
            data_subject = parse_dict(
                resource_type="data_subject",
                resource=raw_data_subject,
                from_server=True,
            )
            assert isinstance(data_subject, DataSubject)
            data_subject_findings = audit_data_subject_attributes(
                data_subject, system.name or ""
            )
            new_findings += data_subject_findings
    return new_findings


def audit_data_subject_attributes(data_subject: DataSubject, system_name: str) -> int:
    """
    Audits the extended attributes for a DataSubject
    """
    data_subject_list = ["rights", "automated_decisions_or_profiling"]
    findings = 0
    for attribute in data_subject_list:
        attribute_is_set = getattr(data_subject, attribute) is not None
        compliance_messaging(
            attribute_is_set, data_subject.fides_key, attribute, system_name
        )
        if not attribute_is_set:
            findings += 1
    return findings


def compliance_messaging(
    compliant: bool, fides_key: str, attribute: str, resource_name: str
) -> None:
    """
    Prints the positive confirmation message for a data map compliant attribute.
    """
    if compliant:
        print(f"{attribute} for {fides_key} in {resource_name} is compliant")
    else:
        echo_red(f"{fides_key} missing {attribute} in {resource_name}.")


def audit_organizations(
    url: str,
    headers: Dict[str, str],
    include_keys: Optional[List] = None,
) -> None:
    """
    Validates the extra attributes for an Organization are
    correctly populated
    """

    organization_resources: Optional[List[FidesModel]]

    if include_keys:
        organization_resources = get_server_resources(
            url, "organization", include_keys, headers
        )
    else:
        raw_organization_resources = list_server_resources(
            url, headers, "organization", exclude_keys=[]
        )
        if raw_organization_resources:
            organization_resources = [
                # Parse this into a FidesModel here so we know we're
                # always using a FidesModel downstream
                parse_dict(
                    resource=organization,
                    resource_type="organization",
                    from_server=True,
                )
                for organization in raw_organization_resources
            ]
        else:
            organization_resources = []

    if not organization_resources:
        print("No organization resources were found.")
        return

    print(f"Found {len(organization_resources)} Organization resource(s) to audit...")

    audit_findings = 0
    for organization in organization_resources:
        print(f"Auditing Organization: {organization.name or organization.fides_key}")
        assert isinstance(organization, Organization)
        new_findings = audit_organization_attributes(organization)
        audit_findings += new_findings
    if audit_findings > 0:
        print(
            f"{audit_findings} issue(s) were detected in auditing organization completeness."
        )
    else:
        echo_green("All audited organization resource(s) compliant!")


def audit_organization_attributes(organization: Organization) -> int:
    """
    Audits the list of specified attributes is set properly on the Organization.
    returns the count of findings
    """

    organization_attributes = [
        "controller",
        "data_protection_officer",
        "representative",
        "security_policy",
    ]
    audit_findings = 0
    for attribute in organization_attributes:
        attribute_is_set = getattr(organization, attribute) is not None
        compliance_messaging(
            attribute_is_set, organization.fides_key, attribute, organization.name or ""
        )
        if not attribute_is_set:
            audit_findings += 1

    return audit_findings
