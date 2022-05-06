from typing import Dict, List

from attr import attr, attrib

from fidesctl.core.api_helpers import get_server_resource, list_server_resources
from fidesctl.core.export_helpers import calculate_data_subject_rights
from fidesctl.core.utils import echo_green, echo_red
from fideslang.models import DataSubject, DataUse, PrivacyDeclaration, System


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
        new_findings = validate_system_attributes(system, url, headers)
        audit_findings = audit_findings + new_findings

    if audit_findings > 0:
        print(f"{audit_findings} issues were detected in auditing system completeness.")
    else:
        echo_green("All systems go!")


def validate_system_attributes(
    system: System,
    url: str,
    headers: Dict[str, str],
) -> int:
    """
    Validates one or multiple attributes are set on a system
    """

    # data_protection_impacts = ["is_required", "progress", "link"]
    data_use_list = ["recipients", "legal_basis", "special_category"]
    data_subject_list = ["rights", "automated_decisions_or_profiling"]

    new_findings = 0
    if system.administrating_department == "Not defined":
        echo_red(
            f"{system.name} should have a responsible group, defined as 'administrating_department'."
        )
        new_findings += 1

    for privacy_declaration in system.privacy_declarations:
        data_use = get_server_resource(
            url, "data_use", privacy_declaration.data_use, headers
        )
        for attribute in data_use_list:
            if getattr(data_use, attribute) is None:
                echo_red(f"{data_use.fides_key} missing {attribute} in {system.name}.")
                new_findings += 1
        for data_subject_fides_key in privacy_declaration.data_subjects:
            data_subject = get_server_resource(
                url, "data_subject", data_subject_fides_key, headers
            )
            for attribute in data_subject_list:
                if getattr(data_subject, attribute) is None:
                    echo_red(
                        f"{data_subject.fides_key} missing {attribute} in {system.name}."
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
