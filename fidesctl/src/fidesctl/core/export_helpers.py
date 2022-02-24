import csv
from datetime import datetime
import shutil

from typing import Dict, List, Tuple, Set

import pandas as pd

from fidesctl.core.api_helpers import get_server_resource
from fidesctl.core.utils import echo_red

from fideslang.models import Taxonomy


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
        "system.privacy_declaration.data_subjects",
        "dataset.data_categories",
        "system.privacy_declaration.data_use.recipients",
        "system.link_to_processor_contract",
        "third_country_combined",
        "system.third_country_safeguards",
        "dataset.retention",
        "organization.link_to_security_policy",
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
    as a dict
    """

    data_use = get_server_resource(url, "data_use", data_use_fides_key, headers)

    formatted_data_use = {
        "name": data_use.name,
        "legal_basis": "N/A",
        "recipients": "N/A",
    }

    try:
        formatted_data_use["legal_basis"] = data_use.legal_basis.value
    except AttributeError:
        echo_red("Legal Basis undefined for specified Data Use, setting as N/A.")

    try:
        formatted_data_use["recipients"] = ", ".join(data_use.recipients)
    except TypeError:
        echo_red("Recipients undefined for specified Data Use, setting as N/A")

    return formatted_data_use


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
