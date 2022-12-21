import csv
import shutil
from datetime import datetime
from os.path import dirname, join
from typing import Dict, List, Set, Tuple

import pandas as pd
from fideslang.models import DataSubject, DataSubjectRightsEnum, DataUse

DATAMAP_TEMPLATE = join(
    dirname(__file__),
    "../templates",
    "fides_datamap_template.xlsx",
)

DATAMAP_COLUMNS = {
    "dataset.name": "Fides Dataset",
    "system.name": "Fides System",
    "system.administrating_department": "Department or Business Function",
    "system.privacy_declaration.data_use.name": "Purpose of Processing",
    "system.joint_controller": "Joint Controller",
    "system.privacy_declaration.data_subjects.name": "Categories of Individuals",
    "unioned_data_categories": "Categories of Personal Data (Fides Taxonomy)",
    "system.privacy_declaration.data_use.recipients": "Categories of Recipients",
    "system.link_to_processor_contract": "Link to Contract with Processor",
    "third_country_combined": "Third Country Transfers",
    "system.third_country_safeguards": "Safeguards for Exceptional Transfers of Personal Data",
    "dataset.retention": "Retention Schedule",
    "organization.link_to_security_policy": "General Description of Security Measures",
    "system.data_responsibility_title": "Role or Responsibility",
    "system.privacy_declaration.data_use.legal_basis": "Article 6 lawful basis for processing personal data",
    "system.privacy_declaration.data_use.special_category": "Article 9 condition for processing special category data",
    "system.privacy_declaration.data_use.legitimate_interest": "Legitimate interests for the processing (if applicable)",
    "system.privacy_declaration.data_use.legitimate_interest_impact_assessment": "Link to record of legitimate interests assessment (if applicable)",
    "system.privacy_declaration.data_subjects.rights_available": "Rights available to individuals",
    "system.privacy_declaration.data_subjects.automated_decisions_or_profiling": "Existence of automated decision-making, including profiling (if applicable)",
    "dataset.source_name": "The source of the personal data (if applicable)",
    "system.data_protection_impact_assessment.is_required": "Data Protection Impact Assessment required?",
    "system.data_protection_impact_assessment.progress": "Data Protection Impact Assessment progress",
    "system.data_protection_impact_assessment.link": "Link to Data Protection Impact Assessment",
}


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
    with open(filepath, "w", encoding="utf-8") as csvfile:
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

        joined_system_dataset_df.sort_values(
            by=[
                "system.name",
                "unioned_data_categories",
            ]
        ).to_excel(
            export_file,
            sheet_name="sheet1",
            index=False,
            header=False,
            startrow=9,
            columns=list(DATAMAP_COLUMNS.keys()),
        )

    return filename


def format_data_uses(data_uses: List[DataUse]) -> Dict[str, Dict[str, str]]:
    """
    This function formats data uses for use when exporting,
    returning the necessary values as a dict. Formatting
    differences exist due to various types allowed across attributes.
    """

    formatted_data_uses = {}
    for data_use in data_uses:
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
            attribute_value = getattr(data_use, attribute)
            if attribute_value is None:
                attribute_value = "N/A"
            elif isinstance(attribute_value, list):
                attribute_value = ", ".join(attribute_value)
            elif attribute == "legitimate_interest":
                if attribute_value is True:
                    attribute_value = getattr(data_use, "name")
                else:
                    attribute_value = "N/A"

            formatted_data_use[attribute] = attribute_value

        formatted_data_uses[data_use.fides_key] = formatted_data_use
    return formatted_data_uses


def format_data_subjects(data_subjects: List[DataSubject]) -> Dict[str, Dict[str, str]]:
    """
    This function formats data subjects from the server, returning the necessary values
    as a list of dicts.

    rights_available is treated differently due to the
    different strategy options available in returning
    the available data subject rights.
    """

    formatted_data_subject_attributes_list = [
        "name",
        "rights_available",
        "automated_decisions_or_profiling",
    ]

    formatted_data_subjects = {}

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

        formatted_data_subject = {
            attribute: data_subject_dict.get(attribute) or "N/A"
            for attribute in formatted_data_subject_attributes_list
        }

        formatted_data_subjects[data_subject.fides_key] = formatted_data_subject

    return formatted_data_subjects


def convert_tuple_to_string(values: Tuple[str, ...]) -> str:
    """
    Takes a tuple of variable length strings and combines them into a comma seperated
    string.

    During the conversion empty strings, "", are converted to "N/A", duplicates are removed,
    then if is checked to see if all values in the tuple are "N/A" if them are the string
    "N/A" is returned. If there are multiple strings presents and some are "N/A", the
    "N/A" is dropped in the resulting string.

    Example:
        - ("CAN", "GBR", "USA") returns "CAN, GBR, USA"
        - ("CAN, GBR", "CAN", "GBR") returns "CAN GBR"
        - ("N/A", "CAN", "GBR") returns "CAN, GBR"
        - ("", "CAN") returns "CAN"
        - ("", "N/A") returns "N/A"
        - ("N/A", "N/A") returns "N/A"
    """
    empty_replaced = {"N/A" if x == "" else x for x in values}
    if empty_replaced == {"N/A"}:
        return "N/A"

    return remove_duplicates_from_comma_separated_column(
        ", ".join((x for x in empty_replaced if x != "N/A"))
    )


def calculate_data_subject_rights(rights: Dict) -> str:
    """
    Calculate and format the data subject individual rights.

    Loads all available rights
    """
    all_rights = DataSubjectRightsEnum
    strategy: str = rights["strategy"]
    data_subject_rights: str
    if strategy == "ALL":
        data_subject_rights = ", ".join(all_rights)
    elif strategy == "INCLUDE":
        included_rights = rights["values"]
        data_subject_rights = ", ".join(included_rights)
    elif strategy == "EXCLUDE":
        excluded_rights = rights["values"]
        included_rights = [
            right for right in all_rights if right not in excluded_rights
        ]
        data_subject_rights = ", ".join(included_rights)
    elif strategy == "NONE":
        data_subject_rights = "No data subject rights listed"

    return data_subject_rights


def remove_duplicates_from_comma_separated_column(comma_separated_string: str) -> str:
    "transform the row using a set to remove duplcation"
    return ", ".join(set(comma_separated_string.split(", ")))


def union_data_categories_in_joined_dataframe(joined_df: pd.DataFrame) -> pd.DataFrame:
    """
    Data Categories can be present in both the System and (optionally) Dataset
    resources, causing duplication when joining them together.

    This function isolates the data categories from each into a new column which
    when unioned together can be used to populate the data map accurately with
    the data categories from both System and Dataset.
    """

    # isolate the system data categories into a new dataframe and create a common column
    joined_df = joined_df.drop(
        [
            "system.privacy_declaration.name",
            "dataset.description",
        ],
        axis=1,
    )
    systems_categories_df = joined_df.drop(
        [
            "dataset.data_categories",
            "dataset.retention",
            "dataset.data_qualifier",
        ],
        axis=1,
    )
    systems_categories_df["dataset.name"] = "N/A"
    systems_categories_df["unioned_data_categories"] = systems_categories_df[
        "system.privacy_declaration.data_categories"
    ]
    systems_categories_df["unioned_data_qualifiers"] = systems_categories_df[
        "system.privacy_declaration.data_qualifier"
    ]
    systems_categories_df["dataset.retention"] = "N/A"
    systems_categories_df["dataset.data_qualifier"] = "N/A"

    # isolate the dataset data categories into a new dataframe and create a common column
    datasets_categories_df = joined_df.drop(
        [
            "system.privacy_declaration.data_categories",
            "system.privacy_declaration.data_qualifier",
        ],
        axis=1,
    )

    datasets_categories_df = datasets_categories_df[
        datasets_categories_df["dataset.name"] != "N/A"
    ]

    datasets_categories_df["unioned_data_qualifiers"] = datasets_categories_df[
        "dataset.data_qualifier"
    ]
    datasets_categories_df["unioned_data_categories"] = datasets_categories_df[
        "dataset.data_categories"
    ]

    # union the two dataframes together to return all data categories
    return pd.concat(
        [
            systems_categories_df.drop(
                ["system.privacy_declaration.data_categories"], axis="columns"
            ),
            datasets_categories_df.drop(["dataset.data_categories"], axis="columns"),
        ]
    ).drop_duplicates()


def get_formatted_data_protection_impact_assessment(
    data_protection_impact_assessment: dict,
) -> dict:
    "Replace None with N/A for consistent formatting of the data map"
    return {
        key: ("N/A" if value is None else value)
        for key, value in data_protection_impact_assessment.items()
    }
