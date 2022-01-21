"""
Exports various resources as data maps.
"""
import csv
from datetime import datetime
from typing import Dict, List, Tuple, Set


from fidesctl.core.api_helpers import get_server_resources
from fidesctl.core.utils import echo_green, get_all_level_fields


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
) -> Set[Tuple[str, str, str, str]]:
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
        )
        for category in data_categories
    }

    return dataset_rows


def generate_dataset_records(
    server_dataset_list: List,
) -> List[Tuple[str, str, str, str]]:
    """
    Returns a list of tuples as records (with expected headers)
    to be exported as csv. The ouput rows consist of unique combinations
    of data categories, data qualifiers, and data uses for the entire dataset
    """

    output_list = [
        (
            "dataset.name",
            "dataset.description",
            "dataset.data_categories",
            "dataset.data_qualifier",
        )
    ]

    # using a set to preserve uniqueness of categories and qualifiers across fields
    unique_data_categories: set = set()

    for dataset in server_dataset_list:
        dataset_name = dataset.name
        dataset_description = dataset.description
        if dataset.data_categories:
            dataset_rows = generate_data_category_rows(
                dataset_name,
                dataset_description,
                dataset.data_qualifier,
                dataset.data_categories,
            )
            unique_data_categories = unique_data_categories.union(dataset_rows)
        for collection in dataset.collections:
            if collection.data_categories:
                dataset_rows = generate_data_category_rows(
                    dataset_name,
                    dataset_description,
                    collection.data_qualifier,
                    collection.data_categories,
                )
                unique_data_categories = unique_data_categories.union(dataset_rows)
            for field in get_all_level_fields(collection.fields):
                if field.data_categories:
                    dataset_rows = generate_data_category_rows(
                        dataset_name,
                        dataset_description,
                        field.data_qualifier,
                        field.data_categories,
                    )
                    unique_data_categories = unique_data_categories.union(dataset_rows)

    # combine found records from the set as a list of tuples/records to be exported
    output_list += list(unique_data_categories)

    return output_list


def export_dataset(
    url: str, dataset_list: List, headers: Dict[str, str], manifests_dir: str, dry: bool
) -> None:
    """
    Exports the required fields from a dataset resource to a csv file.

    The resource is flattened from the server prior to being
    flattened as needed for exporting.
    """
    resource_type = "dataset"
    existing_keys = [resource.fides_key for resource in dataset_list]

    server_resource_list = get_server_resources(
        url, resource_type, existing_keys, headers
    )

    output_list = generate_dataset_records(server_resource_list)

    exported_filename = export_to_csv(output_list, resource_type, manifests_dir)

    if not dry:
        exported_filename = export_to_csv(output_list, resource_type, manifests_dir)

        echo_green(exported_filename + " successfully exported.")
    else:
        echo_green("Output would contain:")
        for record in output_list:
            print(record)


def generate_system_records(
    server_system_list: List,
) -> List[Tuple[str, str, str, str, str, str, str, str]]:
    """
    Takes a list of systems from the server, creating a list of tuples
    to be used as records to be exported. The headers of the csv are
    currently added here as well.
    """
    output_list = [
        (
            "system.name",
            "system.description",
            "system.privacy_declaration.name",
            "system.privacy_declaration.data_categories",
            "system.privacy_declaration.data_uses",
            "system.privacy_declaration.data_subjects",
            "system.privacy_declaration.data_qualifier",
            "system.privacy_declaration.dataset_references",
        )
    ]

    for system in server_system_list:

        for declaration in system.privacy_declarations:
            data_categories = declaration.data_categories or []
            data_subjects = declaration.data_subjects or []
            dataset_references = declaration.dataset_references or []
            cartesian_product_of_declaration = [
                (
                    system.name,
                    system.description,
                    declaration.name,
                    category,
                    declaration.data_use,
                    subject,
                    declaration.data_qualifier,
                    dataset_reference,
                )
                for category in data_categories
                for subject in data_subjects
                for dataset_reference in dataset_references
            ]
            output_list += cartesian_product_of_declaration

    return output_list


def export_system(
    url: str, system_list: List, headers: Dict[str, str], manifests_dir: str, dry: bool
) -> None:
    """
    Exports the required fields from a system resource to a csv file.

    The resource is fetched from the server prior to being
    flattened as needed for exporting.
    """
    resource_type = "system"

    existing_keys = [resource.fides_key for resource in system_list]
    server_resource_list = get_server_resources(
        url, resource_type, existing_keys, headers
    )

    output_list = generate_system_records(server_resource_list)

    if not dry:
        exported_filename = export_to_csv(output_list, resource_type, manifests_dir)

        echo_green(exported_filename + " successfully exported.")
    else:
        echo_green("Output would contain:")
        for record in output_list:
            print(record)
