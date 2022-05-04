from typing import Dict, List

from attr import attr, attrib

from fidesctl.core.api_helpers import list_server_resources
from fidesctl.core.utils import echo_green, echo_red
from fideslang.models import System


def audit_systems(
    url: str,
    headers: Dict[str, str],
    exclude_keys: List,
) -> None:
    """
    Audits the system resources from the server for compliance.

    This should be flexible enough to accept further audits in
    the future and return them as well as being called from other
    audit functions.
    """

    # get the server resources for systems
    system_resources = list_server_resources(
        url, headers, "system", exclude_keys=exclude_keys
    )
    audit_findings = 0
    for system in system_resources:
        print(f"Auditing System: {system.name}")
        new_findings = validate_system_attributes(system)
        audit_findings = audit_findings + new_findings

    if audit_findings > 0:
        print(f"{audit_findings} issues were detected in auditing system completeness.")
    else:
        echo_green("All systems go!")


def validate_system_attributes(system: System) -> int:
    """
    Validates one or multiple attributes are set on a system
    """
    new_findings = 0
    if system.administrating_department == "Not defined":
        echo_red(
            f"{system.name} should have a responsible group, defined as 'administrating_department'."
        )
        new_findings += 1

    return new_findings


def audit_organizations(
    url: str,
    headers: Dict[str, str],
    exclude_keys: List,
) -> None:
    """
    Validates the extra attributes for an Organization are
    correctly populated
    """
    organization_resources = list_server_resources(
        url, headers, "organization", exclude_keys=exclude_keys
    )

    organization_attributes = [
        "controller",
        "data_protection_officer",
        "representative",
        "security_policy",
    ]
    for organization in organization_resources:
        for attribute in organization_attributes:
            if getattr(organization, attribute) is None:
                echo_red(f"{organization.name} missing {attribute}.")
