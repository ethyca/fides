"""This module handles the logic required for applying manifest files to the server."""
from datetime import datetime
from typing import Dict, List, Tuple, Set

import csv

from fidesctl.core.api_helpers import get_server_resources
from fidesctl.core.utils import echo_green, get_all_level_fields


def list_fides_keys(resources: List) -> List:
    """
    Returns a list of fides_keys found in the manifest dir
    """
    existing_keys = [resource.fides_key for resource in resources]
    return existing_keys


def export_to_csv(list_to_export: List, output_type: str, manifests_dir: str) -> None:
    """
    Exports a list of Tuples of any length back to the manifest
    directory as a csv.
    """
    utc_datetime = datetime.utcnow().strftime("%Y-%m-%d-T%H%M%S")
    filename = "".join([utc_datetime, "_", output_type, ".csv"])
    filepath = "/".join([manifests_dir, filename])
    with open(filepath, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(list_to_export)

    echo_green(filename + " successfully exported.")


# def export(
#     url: str,
#     taxonomy: Taxonomy,
#     headers: Dict[str, str],
# ) -> None:
#     """
#     Planned to use this as a potential router for v1
#     """

#     export_list = export_system(url, taxonomy.system, headers)
#     export_to_csv(export_list)


def export_dataset(
    url: str, dataset_list: List, headers: Dict[str, str], manifests_dir: str
) -> None:
    """
    Exports the required fields from a dataset resource to csv
    The resource is extracted from the server prior to being
    flattened as needed for exporting
    """
    resource_type = "dataset"
    existing_keys = list_fides_keys(dataset_list)
    server_resource_list = get_server_resources(
        url, resource_type, existing_keys, headers
    )
    # load the output list with expected headers for the csv
    output_list = [
        (
            "dataset.name",
            "dataset.description",
            "dataset.data_categories",  # from Kelly - unique data categories per data qualifier, per data use per for the entire dataset, per row.
            # "dataset.data_uses",
            # "dataset.data_subjects",
            "dataset.data_qualifier",
        )
    ]
    # using a set here to preserve uniqueness of categories and qualifiers across fields
    unique_data_categories: set = set()

    for dataset in server_resource_list:
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

    output_list += list(unique_data_categories)
    export_to_csv(output_list, resource_type, manifests_dir)


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


def export_system(
    url: str, system_list: List, headers: Dict[str, str], manifests_dir: str
) -> None:
    """
    Exports the required fields from a system resource to csv
    The resource is extracted from the server prior to being
    flattened as needed for exporting
    """
    resource_type = "system"
    existing_keys = list_fides_keys(system_list)
    server_resource_list = get_server_resources(
        url, resource_type, existing_keys, headers
    )

    # load the output list with expected headers for the csv
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

    for system in server_resource_list:

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

    export_to_csv(output_list, resource_type, manifests_dir)

    ### Other method I was testing using pandas,
    ### it seems overly complicated at this point but keeping for PR conversation

    # system_list_of_dicts = []
    # for system in server_resource_list:
    #     system_list_of_dicts.append(system)

    # system_df = pd.merge(
    #     pd.json_normalize(
    #         system_list_of_dicts,
    #         ["privacy_declarations", "dataset_references"],
    #         meta=[
    #             "fides_key",
    #             "name",
    #             "description",
    #             ["privacy_declarations", "data_use"],
    #             ["privacy_declarations", "name"],
    #             ["privacy_declaration", "data_qualifier"],
    #         ],
    #     ),
    #     pd.json_normalize(
    #         system_list_of_dicts,
    #         ["privacy_declarations", "data_categories"],
    #         meta="fides_key",
    #     ),
    #     on="fides_key",
    # ).merge(
    #     pd.json_normalize(
    #         system_list_of_dicts,
    #         ["privacy_declarations", "data_subjects"],
    #         meta="fides_key",
    #     ),
    #     on="fides_key",
    # )
