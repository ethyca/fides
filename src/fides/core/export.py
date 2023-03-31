"""
Exports various resources as data maps.
"""

from typing import Dict, List, Tuple

import pandas as pd
from fideslang.models import ContactDetails, DataFlow, FidesModel

from fides.core.api_helpers import (
    get_server_resource,
    get_server_resources,
    list_server_resources,
)
from fides.core.export_helpers import (
    convert_tuple_to_string,
    export_datamap_to_excel,
    export_to_csv,
    format_data_subjects,
    format_data_uses,
    generate_data_category_rows,
    get_formatted_data_protection_impact_assessment,
    union_data_categories_in_joined_dataframe,
)
from fides.core.utils import echo_green, get_all_level_fields

EMPTY_COLUMN_PLACEHOLDER = "N/A"


def generate_dataset_records(
    server_dataset_list: List,
) -> List[Tuple[str, str, str, str, str, str, str]]:
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
            "dataset.retention",
            "dataset.third_country_transfers",
            "dataset.fides_key",
        )
    ]

    # using a set to preserve uniqueness of categories and qualifiers across fields
    unique_data_categories: set = set()
    for dataset in server_dataset_list:
        if not isinstance(dataset, dict):
            dataset = dataset.dict()

        dataset_name = dataset["name"]
        dataset_description = dataset["description"]
        dataset_fides_key = dataset["fides_key"]
        dataset_retention = dataset["retention"]
        dataset_third_country_transfers = ", ".join(
            dataset["third_country_transfers"] or []
        )
        if dataset["data_categories"]:
            dataset_rows = generate_data_category_rows(
                dataset_name,
                dataset_description,
                dataset["data_qualifier"],
                dataset["data_categories"],
                dataset_retention,
                dataset_third_country_transfers,
                dataset_fides_key,
            )
            unique_data_categories = unique_data_categories.union(dataset_rows)
        for collection in dataset["collections"]:
            collection_retention = collection["retention"] or dataset_retention
            if collection["data_categories"]:
                dataset_rows = generate_data_category_rows(
                    dataset_name,
                    dataset_description,
                    collection["data_qualifier"],
                    collection["data_categories"],
                    collection_retention,
                    dataset_third_country_transfers,
                    dataset_fides_key,
                )
                unique_data_categories = unique_data_categories.union(dataset_rows)
            for field in get_all_level_fields(collection["fields"]):
                if field["data_categories"]:
                    dataset_rows = generate_data_category_rows(
                        dataset_name,
                        dataset_description,
                        field["data_qualifier"],
                        field["data_categories"],
                        field["retention"] or collection_retention,
                        dataset_third_country_transfers,
                        dataset_fides_key,
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

    if not dry:
        exported_filename = export_to_csv(output_list, resource_type, manifests_dir)

        echo_green(exported_filename + " successfully exported.")
    else:
        echo_green("Output would contain:")
        for record in output_list:
            print(record)


def generate_system_records(  # pylint: disable=too-many-nested-blocks, too-many-branches, too-many-statements
    server_resources: Dict[str, List],
) -> Tuple[List[Tuple[str, ...]], Dict[str, str]]:
    """
    Takes a dictionary of resources from the server, returning a list of tuples
    to be used as records to be exported. The headers are defined
    as the first tuple in the result.
    """

    custom_columns = {}
    formatted_data_uses, custom_data_uses = format_data_uses(
        server_resources["data_use"]
    )
    formatted_data_subjects, custom_data_subjects = format_data_subjects(
        server_resources["data_subject"]
    )
    output_list: List[Tuple[str, ...]] = [
        (
            "system.fides_key",
            "system.name",
            "system.description",
            "system.data_responsibility_title",
            "system.administrating_department",
            "system.third_country_transfers",
            "system.system_dependencies",
            "system.ingress",
            "system.egress",
            "system.privacy_declaration.name",
            "system.privacy_declaration.data_categories",
            "system.privacy_declaration.data_use.name",
            "system.privacy_declaration.data_use.legal_basis",
            "system.privacy_declaration.data_use.special_category",
            "system.privacy_declaration.data_use.recipients",
            "system.privacy_declaration.data_use.legitimate_interest",
            "system.privacy_declaration.data_use.legitimate_interest_impact_assessment",
            "system.privacy_declaration.data_subjects.name",
            "system.privacy_declaration.data_subjects.rights_available",
            "system.privacy_declaration.data_subjects.automated_decisions_or_profiling",
            "system.privacy_declaration.data_qualifier",
            "system.data_protection_impact_assessment.is_required",
            "system.data_protection_impact_assessment.progress",
            "system.data_protection_impact_assessment.link",
            "dataset.fides_key",
        )
    ]

    if custom_data_uses:
        keys = list(output_list[0])
        for key, value in custom_data_uses.items():
            key_string = f"system.privacy_declaration.data_use.{key}"
            custom_columns[key_string] = value
            keys.append(key_string)
            output_list[0] = tuple(keys)

    if custom_data_subjects:
        keys = list(output_list[0])
        for key, value in custom_data_subjects.items():
            key_string = f"system.privacy_declaration.data_subjects.{key}"
            custom_columns[key_string] = value
            keys.append(key_string)
            output_list[0] = tuple(keys)

    known_fields = (
        "fides_key",
        "name",
        "description",
        "data_responsibility_title",
        "administrating_department",
        "third_country_transfers",
        "system_dependencies",
        "ingress",
        "egress",
        "privacy_declarations",
        "data_protection_impact_assessment",
        "registry_id",
        "id",
        "updated_at",
        "joint_controller",
        "created_at",
        "organization_fides_key",
        "meta",
        "tags",
        "fidesctl_meta",
        "system_type",
    )

    # list to keep track of header order of custom fields
    system_custom_field_headers = []
    for system in server_resources["system"]:
        system_custom_field_data = {}
        if not isinstance(system, dict):
            system = system.__dict__

        for key, value in system.items():
            if key not in known_fields:
                keys = list(output_list[0])
                key_string = f"system.{key}"
                if key_string not in keys:  # if we havent't seen the key yet
                    keys.append(key_string)  # we add it as a new column
                    output_list[0] = tuple(keys)  # then update our header row
                    custom_columns[key_string] = key
                    # and we also maintain our ordered list of custom field headers
                    system_custom_field_headers.append(key_string)
                if isinstance(value, list):
                    system_custom_field_data[key_string] = ", ".join(value)
                else:
                    system_custom_field_data[key_string] = value

        third_country_list = ", ".join(system.get("third_country_transfers") or [])
        system_dependencies = ", ".join(system.get("system_dependencies") or [])
        if system.get("ingress"):
            if isinstance(system["ingress"], DataFlow):
                system["ingress"] = system["ingress"].dict()
            elif isinstance(system["ingress"], list):
                reformatted = []
                for ingress in system["ingress"]:
                    if isinstance(ingress, DataFlow):
                        reformatted.append(ingress.dict())
                    else:
                        reformatted.append(ingress)
                system["ingress"] = reformatted
        system_ingress = ", ".join(
            [ingress["fides_key"] for ingress in system.get("ingress") or []]
        )
        if system.get("egress"):
            if isinstance(system["egress"], DataFlow):
                system["egress"] = system["egress"].dict()
            elif isinstance(system["egress"], list):
                reformatted = []
                for ingress in system["egress"]:
                    if isinstance(ingress, DataFlow):
                        reformatted.append(ingress.dict())
                    else:
                        reformatted.append(ingress)
                system["egress"] = reformatted
        system_egress = ", ".join(
            [egress["fides_key"] for egress in system.get("egress") or []]
        )
        data_protection_impact_assessment = (
            get_formatted_data_protection_impact_assessment(
                system.get("data_protection_impact_assessment", {})
            )
        )
        if system.get("privacy_declarations"):
            for declaration in system["privacy_declarations"]:
                if not isinstance(declaration, dict):
                    declaration = declaration.dict()

                data_use = formatted_data_uses[declaration["data_use"]]
                data_categories = declaration["data_categories"] or []
                data_subjects = [
                    formatted_data_subjects[data_subject_fides_key]
                    for data_subject_fides_key in declaration["data_subjects"]
                ]
                dataset_references = declaration["dataset_references"] or [
                    EMPTY_COLUMN_PLACEHOLDER
                ]
                cartesian_product_of_declaration_builder = [
                    [
                        system["fides_key"],
                        system["name"],
                        system["description"],
                        system["data_responsibility_title"],
                        system["administrating_department"],
                        third_country_list,
                        system_dependencies,
                        system_ingress,
                        system_egress,
                        declaration["name"],
                        category,
                        data_use["name"],
                        data_use["legal_basis"],
                        data_use["special_category"],
                        data_use["recipients"],
                        data_use["legitimate_interest"],
                        data_use["legitimate_interest_impact_assessment"],
                        subject["name"],
                        subject["rights_available"],
                        subject["automated_decisions_or_profiling"],
                        declaration["data_qualifier"],
                        data_protection_impact_assessment["is_required"],
                        data_protection_impact_assessment["progress"],
                        data_protection_impact_assessment["link"],
                        dataset_reference,
                    ]
                    for category in data_categories
                    for subject in data_subjects
                    for dataset_reference in dataset_references
                ]
                cartesian_product_of_declaration = []

                for product in cartesian_product_of_declaration_builder:
                    if system_custom_field_data:
                        # iterate through our ordered list of custom field headers
                        # and find any corresponding custom field data.
                        # we can't just iterate through the system_custom_field_data
                        # dict because its order may not align with the header order
                        for custom_field_header in system_custom_field_headers:
                            product.append(
                                system_custom_field_data.get(
                                    custom_field_header, EMPTY_COLUMN_PLACEHOLDER
                                )
                            )
                    cartesian_product_of_declaration.append(tuple(product))

                output_list += cartesian_product_of_declaration
        else:
            system_row = [
                system["fides_key"],
                system["name"],
                system["description"],
                system["data_responsibility_title"],
                system["administrating_department"],
                third_country_list,
                system_dependencies,
                system_ingress,
                system_egress,
            ]
            len_no_privacy = len(system_row)
            num_privacy_declaration_fields = 12
            for i in range(num_privacy_declaration_fields):
                system_row.insert(len_no_privacy + i, EMPTY_COLUMN_PLACEHOLDER)

            system_row.append(data_protection_impact_assessment["is_required"])
            system_row.append(data_protection_impact_assessment["progress"])
            system_row.append(data_protection_impact_assessment["link"])
            system_row.append(EMPTY_COLUMN_PLACEHOLDER)

            # iterate through our ordered list of custom field headers
            # and find any corresponding custom field data.
            # we can't just iterate through the system_custom_field_data
            # dict because its order may not align with the header order
            for custom_field_header in system_custom_field_headers:
                system_row.append(
                    system_custom_field_data.get(
                        custom_field_header, EMPTY_COLUMN_PLACEHOLDER
                    )
                )

            # also add n/a for the dataset reference
            output_list += [tuple(system_row)]

    return output_list, custom_columns


def export_system(
    url: str, system_list: List, headers: Dict[str, str], manifests_dir: str, dry: bool
) -> None:
    """
    Exports the required fields from a system resource to a csv file.

    Currently limited to systems found in the specified directory.

    Required resources are fetched from the server prior to being
    flattened as needed for exporting.
    """
    resource_type = "system"

    server_resources = {}
    existing_keys = [resource.fides_key for resource in system_list]
    server_resources[resource_type] = get_server_resources(
        url, resource_type, existing_keys, headers
    )

    data_use_fides_keys = [
        privacy_declaration.data_use
        for system in server_resources[resource_type]
        for privacy_declaration in system.privacy_declarations
    ]
    server_resources["data_use"] = get_server_resources(
        url, "data_use", list(set(data_use_fides_keys)), headers
    )

    data_subject_fides_keys = [
        data_subject
        for system in server_resources[resource_type]
        for privacy_declaration in system.privacy_declarations
        for data_subject in privacy_declaration.data_subjects
    ]

    server_resources["data_subject"] = get_server_resources(
        url, "data_subject", list(set(data_subject_fides_keys)), headers
    )

    output_list, _ = generate_system_records(server_resources)

    if not dry:
        exported_filename = export_to_csv(output_list, resource_type, manifests_dir)

        echo_green(exported_filename + " successfully exported.")
    else:
        echo_green("Output would contain:")
        for record in output_list:
            print(record)


def generate_contact_records(
    server_organization_list: List,
) -> List:
    """
    Takes a list of organizations and breaks out the individual
    fields to be returned.
    """
    output_list: List[Tuple] = [
        (
            "Organization Name and Contact Detail",
            "",
            "Data Protection Officer (if applicable)",
            "",
            "Representative (if applicable)",
            "",
        )
    ]

    # currently the output file will only truly support a single organization
    # need to better understand the use case for multiple and how to handle
    for organization in server_organization_list:
        if not isinstance(organization, dict):
            organization = organization.dict()

        fields = tuple(ContactDetails().dict().keys())

        get_values = (
            lambda x: tuple(x.values())
            if x
            else tuple(ContactDetails().dict().values())
        )
        controller = get_values(organization["controller"])
        data_protection_officer = get_values(organization["data_protection_officer"])
        representative = get_values(organization["representative"])

        contact_details = list(
            zip(
                fields,
                controller,
                fields,
                data_protection_officer,
                fields,
                representative,
            )
        )

        output_list += contact_details

    return output_list


def export_organization(
    url: str,
    organization_list: List,
    headers: Dict[str, str],
    manifests_dir: str,
    dry: bool,
) -> None:
    """
    Exports the required fields from a system resource to a csv file.

    The resource is fetched from the server prior to being
    flattened as needed for exporting.
    """
    resource_type = "organization"

    existing_keys = [resource.fides_key for resource in organization_list]

    server_resource_list = get_server_resources(
        url, resource_type, existing_keys, headers
    )

    output_list = generate_contact_records(server_resource_list)

    if not dry:
        exported_filename = export_to_csv(output_list, resource_type, manifests_dir)

        echo_green(exported_filename + " successfully exported.")
    else:
        echo_green("Output would contain:")
        for record in output_list:
            print(record)


def build_joined_dataframe(
    server_resource_dict: Dict[str, List],
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Return joined dataframes for datamap export

    Currently we have a few unhandled columns that exist in the template
    Including those here manually for now is required to use the append
    function built in to pandas
    """

    # systems

    system_output_list, custom_columns = generate_system_records(server_resource_dict)
    systems_df = pd.DataFrame.from_records(system_output_list)
    systems_df.columns = systems_df.iloc[0]
    systems_df = systems_df[1:]

    # datasets

    dataset_output_list = generate_dataset_records(server_resource_dict["dataset"])
    datasets_df = pd.DataFrame.from_records(dataset_output_list)
    datasets_df.columns = datasets_df.iloc[0]
    datasets_df = datasets_df[1:]

    # merge systems and datasets
    joined_df = systems_df.merge(datasets_df, how="left", on=["dataset.fides_key"])
    joined_df.fillna(EMPTY_COLUMN_PLACEHOLDER, inplace=True)
    ## create a set of third_country attrs to combine as a single entity
    joined_df["third_country_combined"] = [
        convert_tuple_to_string(i)
        for i in zip(
            joined_df["system.third_country_transfers"].map(str),
            joined_df["dataset.third_country_transfers"],
        )
    ]

    # restructure the joined dataframe to represent system and dataset data categories appropriately
    joined_df = union_data_categories_in_joined_dataframe(joined_df)

    delete_df = joined_df[
        [
            "system.name",
            "system.privacy_declaration.data_use.name",
            "system.privacy_declaration.data_subjects.name",
            "unioned_data_categories",
        ]
    ][
        joined_df.groupby(
            [
                "system.name",
                "system.privacy_declaration.data_use.name",
                "system.privacy_declaration.data_subjects.name",
                "unioned_data_categories",
            ]
        )["dataset.name"].transform("count")
        > 1
    ].drop_duplicates()

    delete_df["dataset.name"] = EMPTY_COLUMN_PLACEHOLDER

    joined_df = (
        pd.merge(joined_df, delete_df, indicator=True, how="outer")
        .query('_merge=="left_only"')
        .drop("_merge", axis=1)
    )

    # model empty columns until implemented as part of appending to template
    joined_df["system.joint_controller"] = ""
    joined_df["system.third_country_safeguards"] = ""
    joined_df["system.link_to_processor_contract"] = ""

    if not isinstance(server_resource_dict["organization"][0], dict):
        server_resource_dict["organization"][0] = server_resource_dict["organization"][
            0
        ].dict()

    joined_df["organization.link_to_security_policy"] = (
        server_resource_dict["organization"][0]["security_policy"] or ""
    )
    joined_df["dataset.source_name"] = joined_df["dataset.name"]

    return joined_df, custom_columns


def export_datamap(
    url: str,
    headers: Dict[str, str],
    organization_fides_key: str,
    output_directory: str,
    dry: bool,
    to_csv: bool,
) -> None:
    """
    Exports the required fields from a system resource to a csv file.

    The resource is fetched from the server prior to being
    flattened as needed for exporting.
    """

    # load resources from server, filtered by organization
    server_resource_dict = {
        "organization": [
            get_server_resource(url, "organization", organization_fides_key, headers)
        ]
    }
    # Verify this isn't dropping records on the joins
    for resource_type in ["system", "dataset", "data_subject", "data_use"]:
        server_resources = list_server_resources(
            url,
            headers,
            resource_type,
            exclude_keys=[],
        )

        if not server_resources:
            continue

        filtered_server_resources = []
        for resource in server_resources:
            key = (
                resource.organization_fides_key
                if isinstance(resource, FidesModel)
                else resource["organization_fides_key"]
            )

            if key == organization_fides_key:
                filtered_server_resources.append(resource)

        server_resource_dict[resource_type] = filtered_server_resources

    # transform the resources to join a system and referenced datasets
    joined_system_dataset_df, _ = build_joined_dataframe(server_resource_dict)

    if not dry and not to_csv:
        # build an organization dataframe if exporting to excel
        organization_df = pd.DataFrame.from_records(
            generate_contact_records(server_resource_dict["organization"])
        )
        organization_df.columns = organization_df.iloc[0]
        organization_df = organization_df[1:]

        exported_filename = export_datamap_to_excel(
            organization_df, joined_system_dataset_df, output_directory
        )
        echo_green(exported_filename + " successfully exported.")
    else:
        output_list = [tuple(joined_system_dataset_df.columns)]
        output_list += list(joined_system_dataset_df.itertuples(index=False, name=None))

        if dry:
            echo_green("Output would contain:")
            for record in output_list:
                print(record)
        else:
            exported_filename = export_to_csv(output_list, "datamap", output_directory)
            echo_green(exported_filename + " successfully exported.")
