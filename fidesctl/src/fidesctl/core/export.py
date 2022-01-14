"""This module handles the logic required for applying manifest files to the server."""
from datetime import datetime
from pprint import pprint
from typing import Dict, List, Tuple, Optional

import csv

from fidesctl.cli.utils import handle_cli_response
from fidesctl.core import api
from fidesctl.core.api_helpers import get_server_resources
from fidesctl.core.utils import echo_green
from fideslang import FidesModel, Taxonomy


def list_fides_keys(resources: List):
    existing_keys = [resource.fides_key for resource in resources]
    return existing_keys


def export_csv(
    list_to_export: List[Tuple], output_type: str, manifests_dir: str
) -> None:
    utc_datetime = datetime.utcnow().strftime("%Y-%m-%d-T%H%M%S")
    filename = "".join([utc_datetime, "_", output_type, ".csv"])
    filepath = "/".join([manifests_dir, filename])
    with open(filepath, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(list_to_export)


# def export(
#     url: str,
#     taxonomy: Taxonomy,
#     headers: Dict[str, str],
# ) -> None:
#     """
#     Planned to use this as a potential router for v1
#     """

#     export_list = export_system(url, taxonomy.system, headers)
#     export_csv(export_list)


def export_system(
    url: str, system_list: List, headers: Dict[str, str], manifests_dir: str
) -> None:
    resource_type = "system"
    existing_keys = list_fides_keys(system_list)
    server_resource_list = get_server_resources(
        url, resource_type, existing_keys, headers
    )

    system_headers = [
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

    output_list = []
    output_list += system_headers

    for system in system_list:

        system_name = system.name
        system_description = system.description

        for declaration in system.privacy_declarations:
            data_categories = declaration.data_categories or []
            data_subjects = declaration.data_subjects or []
            dataset_references = declaration.dataset_references or []
            cartesian_product_of_declaration = [
                (
                    system_name,
                    system_description,
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

    export_csv(output_list, resource_type, manifests_dir)

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
