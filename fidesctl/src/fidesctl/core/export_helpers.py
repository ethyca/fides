import csv
from datetime import datetime
from enum import Enum
import shutil

from typing import Dict, List, Tuple, Set

import pandas as pd

from fideslang.models import DataSubjectRights, DataSubjectRightsEnum, Taxonomy
from fidesctl.core.api_helpers import get_server_resource, get_server_resources
from fidesctl.core.utils import echo_red


DATAMAP_TEMPLATE = "src/fidesctl/templates/fides_datamap_template.xlsx"


def export_to_csv(
    list_to_export: List, resource_exported: str, manifests_dir: str
) -> str:
    """
    Exports a list of Tuples of any length back to the manifest
    directory as a csv.
    """
    utc_datetime = datetime.utcnow().strftime("%Y-%m-%d-T%H%M%S")
    filename = f"{utc_datetime}_{resource_exported}.csv"
    filepath = f"{manifests_dir}/{filename}"
    with open(filepath, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(list_to_export)

    return filename


def generate_data_category_rows(
    dataset_name: str,
    dataset_description: str,
    data_qualifier: str,
    data_categories: List,
    data_retention: str,
    dataset_third_country_transfers: str,
    dataset_fides_key: str,
) -> Set[Tuple[str, str, str, str, str, str, str]]:
    """
    Set comprehension to capture categories from any
    of the possible levels in a dataset resource.

    Returns a set of tuples to be unioned with the
    overall set to be exported.
    """
    dataset_rows = {
        (
            dataset_name,
            dataset_description,
            category,
            data_qualifier,
            data_retention,
            dataset_third_country_transfers,
            dataset_fides_key,
        )
        for category in data_categories
    }

    return dataset_rows


def export_datamap_to_excel(
    organization_df: pd.DataFrame,
    joined_system_dataset_df: pd.DataFrame,
    manifests_dir: str,
) -> str:
    """
    Creates a copy from the existing datamap template and generates
    an exported datamap based on applied fides resources. Uses two
    dataframes, one for the organization and one for the joined
    system and dataset resources.
    """
    utc_datetime = datetime.utcnow().strftime("%Y-%m-%d-T%H%M%S")
    filename = f"{utc_datetime}_datamap.xlsx"
    filepath = f"{manifests_dir}/{filename}"

    shutil.copy(DATAMAP_TEMPLATE, filepath)

    # append data to the copied template
    output_columns = [
        "dataset.name",
        "system.name",
        "system.administrating_department",
        "system.privacy_declaration.data_use.name",
        "system.joint_controller",
        "system.privacy_declaration.data_subjects.name",
        "dataset.data_categories",
        "system.privacy_declaration.data_use.recipients",
        "system.link_to_processor_contract",
        "third_country_combined",
        "system.third_country_safeguards",
        "dataset.retention",
        "organization.link_to_security_policy",
        "system.data_responsibility_title",
        "system.privacy_declaration.data_use.legal_basis",
        "system.privacy_declaration.data_use.special_category",
        "system.privacy_declaration.data_use.legitimate_interest",
        "system.privacy_declaration.data_use.legitimate_interest_impact_assessment",
        "system.privacy_declaration.data_subjects.rights_available",
        "system.privacy_declaration.data_subjects.automated_decisions_or_profiling",
        "dataset.name",
    ]
    # pylint: disable=abstract-class-instantiated
    with pd.ExcelWriter(
        filepath, mode="a", if_sheet_exists="overlay"
    ) as export_file:  # pylint: enable=abstract-class-instantiated
        organization_df.to_excel(
            export_file,
            sheet_name="sheet1",
            index=False,
            header=False,
            startrow=2,
            startcol=2,
        )

        joined_system_dataset_df.to_excel(
            export_file,
            sheet_name="sheet1",
            index=False,
            header=False,
            startrow=9,
            columns=output_columns,
        )

    return filename


def get_formatted_data_use(
    url: str, headers: Dict[str, str], data_use_fides_key: str
) -> Dict[str, str]:
    """
    This function retrieves the data use from the server
    and formats the results, returning the necessary values
    as a dict. With multiple types possible, some introspection
    is done to handle each accordingly.
    """

    data_use = get_server_resource(url, "data_use", data_use_fides_key, headers)

    formatted_data_use = {
        "name": data_use.name,
    }

    for attribute in [
        "legal_basis",
        "special_category",
        "recipients",
        "legitimate_interest_impact_assessment",
        "legitimate_interest",
    ]:
        try:
            attribute_value = getattr(data_use, attribute)
            if attribute_value is None:
                attribute_value = "N/A"
            elif isinstance(attribute_value, Enum):
                attribute_value = attribute_value.value
            elif isinstance(attribute_value, list):
                attribute_value = ", ".join(attribute_value)
            elif attribute == "legitimate_interest":
                if attribute_value is True:
                    attribute_value = getattr(data_use, "name")
                else:
                    attribute_value = "N/A"

            formatted_data_use[attribute] = attribute_value
        except AttributeError:
            echo_red(f"{attribute} undefined for specified Data Use, setting as N/A.")

    return formatted_data_use


def get_formatted_data_subjects(
    url: str, headers: Dict[str, str], data_subjects_fides_keys: List[str]
) -> List[Dict[str, str]]:
    """
    This function retrieves the data subjects from the server
    and formats the results, returning the necessary values
    as a list of dicts
    """

    data_subjects = get_server_resources(
        url, "data_subject", data_subjects_fides_keys, headers
    )

    formatted_data_subject_attributes_list = [
        "name",
        "rights_available",
        "automated_decisions_or_profiling",
    ]

    formatted_data_subjects_list = []  # empty list to populate and return

    for data_subject in data_subjects:
        data_subject_dict = data_subject.dict()
        formatted_data_subject = dict(
            zip(
                formatted_data_subject_attributes_list,
                [
                    "N/A",
                ]
                * len(formatted_data_subject_attributes_list),
            )
        )

        # calculate and format data subject rights as applicable
        if data_subject_dict["rights"]:
            data_subject_dict["rights_available"] = calculate_data_subject_rights(
                data_subject_dict["rights"]
            )
        else:
            data_subject_dict["rights_available"] = "No data subject rights listed"

        for attribute in formatted_data_subject_attributes_list:
            try:
                formatted_data_subject[attribute] = (
                    data_subject_dict[attribute] or "N/A"
                )
            except AttributeError:
                echo_red(
                    f"{attribute} undefined for specified Data Subject, setting as N/A."
                )

        formatted_data_subjects_list.append(formatted_data_subject)

    return formatted_data_subjects_list


def calculate_data_subject_rights(rights: DataSubjectRights) -> str:
    """
    Calculate and format the data subject individual rights.

    Loads all available rights
    """
    all_rights = [right.value for right in DataSubjectRightsEnum]
    strategy: str = rights["strategy"].value
    data_subject_rights: str
    if strategy == "ALL":
        data_subject_rights = ", ".join(all_rights)
    elif strategy == "INCLUDE":
        included_rights = [right.value for right in rights["values"]]
        data_subject_rights = ", ".join(included_rights)
    elif strategy == "EXCLUDE":
        excluded_rights = [right.value for right in rights["values"]]
        included_rights = [
            right for right in all_rights if right not in excluded_rights
        ]
        data_subject_rights = ", ".join(included_rights)
    elif strategy == "NONE":
        data_subject_rights = "No data subject rights listed"

    return data_subject_rights


def get_datamap_fides_keys(taxonomy: Taxonomy) -> Dict:
    """
    Gathers all fides keys for an organization, systems,
    and datasets based on the resources found in the
    provided taxonomy built from manifests.
    """
    taxonomy_keys_dict = {}
    taxonomy_keys_dict["organization"] = [
        resource.fides_key for resource in taxonomy.organization
    ]
    taxonomy_keys_dict["system"] = [resource.fides_key for resource in taxonomy.system]
    taxonomy_keys_dict["dataset"] = [
        resource.fides_key for resource in taxonomy.dataset
    ]
    return taxonomy_keys_dict


def remove_duplicates_from_comma_separated_column(comma_separated_string: str) -> str:
    "transform the row using a set to remove duplcation"
    return ", ".join(set(comma_separated_string.split(", ")))
