"""
This script is a utility for interactively annotating data categories in the dataset manifest
"""

from typing import List, Union

import click
from fideslang import manifests
from fideslang.manifests import ingest_manifests
from fideslang.models import Dataset, DatasetCollection, DatasetField
from fideslang.parse import parse_dict
from fideslang.validation import FidesKey, FidesValidationError, validate_fides_key

from fides.common.utils import echo_green
from fides.config import FidesConfig
from fides.core import api_helpers
from fides.core.utils import get_all_level_fields


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
        validate_fides_key(category)
        if category not in valid_categories:
            raise ValueError


def get_data_categories_annotation(
    dataset_member: Union[Dataset, DatasetCollection, DatasetField],
    valid_categories: List[str],
    validate: bool = True,
) -> List[FidesKey]:
    """
    Request the user's input to supply a list of data categories

    Args:
        dataset_member: A member of a dataset [dataset, collection, field]
        valid_categories: a list of the valid data categories
        validate: flag to check user inputs for formatting and data category presence

    Returns:
        List of the user's input
    """
    msg = f"""Enter comma separated data categories for [{dataset_member.name}] [s: skip, q: quit]"""
    user_response = [input.strip() for input in click.prompt(msg).split(",")]

    if user_response == ["s"]:
        return []

    if user_response == ["q"]:
        if click.confirm(
            "Are you sure you want to quit annotating the dataset? (progress will be saved)"
        ):
            raise AnnotationAbortError
        return get_data_categories_annotation(dataset_member, valid_categories)

    if validate:
        try:
            validate_data_categories(user_response, valid_categories)
        except (FidesValidationError, ValueError):
            click.secho(
                f"[{user_response}] is not a valid data category, please re-confirm and try again!",
                fg="red",
            )
            user_response = get_data_categories_annotation(
                dataset_member, valid_categories
            )

    return [str(FidesKey(value)) for value in user_response]  # type: ignore


def annotate_dataset(
    config: FidesConfig,
    dataset_file: str,
    resource_type: str = "data_category",
    annotate_all: bool = False,
    validate: bool = True,
    include_null: bool = False,
) -> None:
    """
    Given a dataset.yml-like file, walk the user through an interactive cli to provide data categories
    for members of the dataset that do not have any specified
    Args:
        dataset_file: the file name for the dataset to annotate
        resource_type: the type of data resource to point to for assistance (via visualization web page)
        annotate_all: flag to annotate all members of a dataset (default False: only annotate fields)
        validate: flag to check user inputs for formatting and data category presence
        include_null: flag to write out all empty attributes with null (default False: only write populated attributes)

    Returns:
        Write the amended dataset file in place
    """
    output_dataset = []

    datasets = [
        Dataset.model_validate(dataset)
        for dataset in ingest_manifests(dataset_file)["dataset"]
    ]
    raw_resources = api_helpers.list_server_resources(
        url=str(config.cli.server_url),
        resource_type=resource_type,
        headers=config.user.auth_header
        or {"Authorization": "Bearer fakekey"},  # Alternate header required for mypy
        exclude_keys=[],
    )

    if not raw_resources:
        click.secho(
            "No server resources were found.",
            fg="red",
        )
        return

    resources = [
        parse_dict(resource_type=resource_type, resource=resource)
        for resource in raw_resources
    ]

    existing_categories: List[str] = [resource.fides_key for resource in resources]

    for dataset in datasets:
        current_dataset = Dataset.model_validate(dataset)
        try:
            click.secho(f"\n####\nAnnotating Dataset: [{current_dataset.name}]")

            # Check for data_categories at the Dataset level
            if annotate_all and not dataset.data_categories:
                click.secho(f"Database [{dataset.name}] has no data categories")
                dataset.data_categories = get_data_categories_annotation(
                    dataset_member=dataset,
                    valid_categories=existing_categories,
                    validate=validate,
                )

            annotate_collections(
                current_dataset,
                existing_categories,
                annotate_all,
                validate,
            )

            if include_null:
                output_dataset.append(current_dataset.model_dump(mode="json"))
            else:
                output_dataset.append(
                    current_dataset.model_dump(mode="json", exclude_none=True)
                )
        except AnnotationAbortError:
            if include_null:
                output_dataset.append(current_dataset.model_dump(mode="json"))
            else:
                output_dataset.append(
                    current_dataset.model_dump(mode="json", exclude_none=True)
                )
            break
    manifests.write_manifest(dataset_file, output_dataset, "dataset")
    echo_green("Annotation process complete.")


def annotate_collections(
    current_dataset: Dataset,
    existing_categories: List[str],
    annotate_all: bool,
    validate: bool,
) -> None:
    """
    Check for data_categories at the collections level
    """

    for table in current_dataset.collections:
        click.secho(f"####\nAnnotating Table: [{table.name}]\n")
        if annotate_all and not table.data_categories:
            click.secho(f"Table [{table.name}] has no data categories")
            table.data_categories = get_data_categories_annotation(
                dataset_member=table,
                valid_categories=existing_categories,
                validate=validate,
            )

        annotate_fields(table, existing_categories, validate)


def annotate_fields(
    table: DatasetCollection,
    existing_categories: List[str],
    validate: bool,
) -> None:
    """
    Check for data_categories at the field level
    """
    for field in get_all_level_fields(table.fields):
        if not field.data_categories:
            click.secho(
                f"Field [{table.name}.{field.name}] has no data categories\n",
                fg="red",
            )

            user_categories = get_data_categories_annotation(
                dataset_member=field,
                valid_categories=existing_categories,
                validate=validate,
            )

            click.secho(
                f"""Setting data categories for {table.name}.{field.name} to:
            {user_categories}\n""",
                fg="green",
            )

            field.data_categories = user_categories
