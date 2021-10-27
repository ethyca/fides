"""
This script is a utility for interactively annotating data categories in the dataset manifest
"""

import pathlib
from typing import Union, List

import click

from fidesctl.core import parse as core_parse
from fidesctl.core import visualize
from fideslang import manifests
from fideslang.models import Dataset, DatasetCollection, DatasetField, FidesKey
from fideslang.validation import FidesValidationError
from fidesapi.crud import list_resource
from fidesapi.sql_models import sql_model_map


DATASET_KEY = "dataset"
DATA_CATEGORY_KEY = "data_category"
FIDES_KEY = "fides_key"


class AnnotationAbortError(Exception):
    """
    Custom exception to handle mid annotation abort
    """


def validate_data_categories(
    categories: List[str], valid_categories: List[str]
) -> None:
    """
    Check to see if each category in a list is valid
    Args:
        categories: list of category strings to check
        valid_categories: list of valid categories

    Returns:

    """
    for category in categories:
        # check for valid format of string
        _ = FidesKey.validate(category)
        # throws FidesValidationError if malformed
        if category not in valid_categories:
            raise ValueError


def get_data_categories_annotation(
    dataset_member: Union[Dataset, DatasetCollection, DatasetField],
    valid_categories: List[str],
    validate: bool = True,
) -> List[str]:
    """
    Request the user's input to supply a list of data categories

    TODO: data_category validation would be nice. to let them know if what they've provided is okay

    Args:
        dataset_member: A member of a dataset [dataset, collection, field]
        valid_categories: a list of the valid data categories
        validate: flag to check user inputs for formatting and data category presence

    Returns:
        List of the user's input
    """
    msg = f"""Enter comma separated data categories for [{dataset_member.name}] [Enter: skip, q: quit]"""
    user_response = click.prompt(msg, default=[])
    if user_response:
        if user_response.lower() == "q":
            if click.confirm(
                "Are you sure you want to quit annotating the dataset? (progress will be saved)"
            ):
                raise AnnotationAbortError
            user_response = get_data_categories_annotation(
                dataset_member, valid_categories
            )
        if validate:
            try:
                validate_data_categories(user_response, valid_categories)
            except (FidesValidationError, ValueError):
                click.secho(
                    f"[{user_response}] contains invalid categories, please re-enter!",
                    fg="red",
                )
                user_response = get_data_categories_annotation(
                    dataset_member, valid_categories
                )

        return [i.strip() for i in user_response.split(",")]
    return []


def annotate_dataset(
    dataset_file: str,
    resource_type: str = "data_category",
    annotate_all: bool = False,
    file_split: bool = True,
    validate: bool = True,
) -> None:
    """
    Given a dataset.yml-like file, walk the user through an interactive cli to provide data categories
    for members of the dataset that do not have any specified
    Args:
        dataset_file: the file name for the dataset to annotate
        resource_type: the type of data resource to point to for assistance (via visualization web page)
        annotate_all: flag to annotate all members of a dataset (default False: only annotate fields)
        file_split: flag to split multiple datasets into individual, self-named dataset yaml files
        validate: flag to check user inputs for formatting and data category presence

    Returns:
        Write the amended dataset file in place
    """
    output_filename = dataset_file

    # Make the user aware of the data_categories visualizer
    click.secho(
        f"""For reference, open the data category visualizer at either (localhost if running container):
        {visualize.get_visualize_url(resource_type, "graphs")}
        {visualize.get_visualize_url(resource_type, "text")}
    """,
        fg="green",
    )

    # load in the dataset
    datasets = core_parse.ingest_manifests(dataset_file)[DATASET_KEY]

    # load in valid data categories
    available_categories = [
        resource.__dict__[FIDES_KEY]
        for resource in list_resource(sql_model_map[resource_type])
    ]

    for dataset in datasets:  # iterate through each database/schema found
        current_dataset = Dataset(**dataset)
        click.secho(f"\n####\nAnnotating Dataset: [{current_dataset.name}]")

        if len(datasets) > 1 and file_split:
            # if more than one dataset is in the list, each dataset will be split into separate files
            output_filename = str(
                pathlib.Path(output_filename)
                .parents[0]
                .joinpath(f"{current_dataset.name}.yml")
            )

        if annotate_all and not current_dataset.data_categories:
            click.secho(f"Database [{current_dataset.name}] has no data categories")
            current_dataset.data_categories = get_data_categories_annotation(
                current_dataset, available_categories, validate=validate
            )

        for table in current_dataset.collections:
            click.secho(f"####\nAnnotating Table: [{table.name}]\n")
            if annotate_all and not table.data_categories:
                click.secho(f"Table [{table.name}] has no data categories")
                table.data_categories = get_data_categories_annotation(
                    table, available_categories, validate=validate
                )

            for field in table.fields:
                if not field.data_categories:
                    click.secho(
                        f"Field [{table.name}.{field.name}] has no data categories\n"
                    )
                    try:
                        user_categories = get_data_categories_annotation(
                            field, available_categories, validate=validate
                        )
                        click.secho(
                            f"""Setting data categories for {table.name}.{field.name} to:
                        {user_categories}\n"""
                        )
                        field.data_categories = user_categories
                    except AnnotationAbortError:
                        break
            else:
                continue
            break
        else:
            continue

        manifests.write_manifest(output_filename, current_dataset.dict(), DATASET_KEY)
