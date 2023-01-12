"""Contains the annotate group of CLI commands for fides."""

import click

from fides.cli.utils import with_analytics
from fides.core import annotate_dataset as _annotate_dataset


@click.group(name="annotate")
@click.pass_context
def annotate(ctx: click.Context) -> None:
    """
    Annotate fides resource types
    """


@annotate.command(name="dataset")
@click.pass_context
@click.argument("input_filename", type=str)
@click.option(
    "-a",
    "--all-members",
    is_flag=True,
    help="Annotate all dataset members, not just fields",
)
@click.option(
    "-v",
    "--validate",
    is_flag=True,
    default=False,
    help="Strictly validate annotation inputs.",
)
@with_analytics
def annotate_dataset(
    ctx: click.Context, input_filename: str, all_members: bool, validate: bool
) -> None:
    """
    Guided flow for annotating datasets. The dataset file will be edited in-place.
    """
    config = ctx.obj["CONFIG"]
    _annotate_dataset.annotate_dataset(
        config=config,
        dataset_file=input_filename,
        annotate_all=all_members,
        validate=validate,
    )
