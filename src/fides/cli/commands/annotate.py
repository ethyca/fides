"""Contains the annotate group of CLI commands for fides."""

import rich_click as click

from fides.cli.utils import with_analytics
from fides.core import annotate_dataset as _annotate_dataset


@click.group(name="annotate")
@click.pass_context
def annotate(ctx: click.Context) -> None:
    """
    Interactively annotate Fides resources.
    """


@annotate.command(name="dataset")  # type: ignore
@click.pass_context
@click.argument("input_filename", type=str)
@click.option(
    "-a",
    "--all-members",
    is_flag=True,
    help="Annotate all parts of the dataset including schemas and tables.",
)
@click.option(
    "-v",
    "--validate",
    is_flag=True,
    default=False,
    help="Validate annotation inputs.",
)
@with_analytics
def annotate_dataset(
    ctx: click.Context, input_filename: str, all_members: bool, validate: bool
) -> None:
    """
    Interactively annotate a dataset file in-place.
    """
    config = ctx.obj["CONFIG"]
    _annotate_dataset.annotate_dataset(
        config=config,
        dataset_file=input_filename,
        annotate_all=all_members,
        validate=validate,
    )
