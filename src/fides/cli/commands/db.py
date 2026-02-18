"""Contains the db group of the commands for fides."""

import rich_click as click

from fides.api.db.session import get_db_session
from fides.api.util.consent_encryption_migration import (
    migrate_consent_encryption as run_consent_encryption_migration,
)
from fides.cli.options import yes_flag
from fides.cli.utils import with_analytics, with_server_health_check
from fides.common.utils import echo_red, handle_cli_response
from fides.core import api as _api


@click.group(name="db")
@click.pass_context
def database(ctx: click.Context) -> None:
    """
    Run actions against the application database.
    """


@database.command(name="init", deprecated=True)
@click.pass_context
@with_analytics
@with_server_health_check
def db_init(ctx: click.Context) -> None:
    """
    Runs all upgrade migrations for the Fides database.

    Will also automatically initialize a fresh database.

    **WARNING**: Deprecated, use `upgrade` instead.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _api.db_action(
            server_url=config.cli.server_url,
            headers=config.user.auth_header,
            action="upgrade",
        )
    )


@database.command(name="upgrade")
@click.pass_context
@with_analytics
@with_server_health_check
def db_upgrade(ctx: click.Context) -> None:
    """
    Runs all upgrade migrations for the Fides database.

    Will also automatically initialize a fresh database.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _api.db_action(
            server_url=config.cli.server_url,
            headers=config.user.auth_header,
            action="upgrade",
        )
    )


@database.command(name="reset")
@click.pass_context
@yes_flag
@with_analytics
@with_server_health_check
def db_reset(ctx: click.Context, yes: bool) -> None:
    """
    Reset the database back to its initial state.
    """
    config = ctx.obj["CONFIG"]
    if yes:
        are_you_sure = "y"
    else:
        echo_red(
            "This will drop all data from the Fides database and reload the default taxonomy!"
        )
        are_you_sure = input("Are you sure [y/n]? ")

    if are_you_sure.lower() == "y":
        handle_cli_response(
            _api.db_action(
                server_url=config.cli.server_url,
                headers=config.user.auth_header,
                action="reset",
            )
        )
    else:
        print("Aborting!")


@database.command(name="migrate-consent-encryption")
@click.option(
    "--direction",
    type=click.Choice(["encrypt", "decrypt"], case_sensitive=False),
    required=True,
    help="Whether to encrypt or decrypt the record_data column.",
)
@click.option(
    "--batch-size",
    default=5000,
    type=int,
    help="Rows per batch.",
)
@click.pass_context
def migrate_consent_encryption(
    ctx: click.Context, direction: str, batch_size: int
) -> None:
    """
    Encrypt or decrypt v3 privacy preferences record_data.

    Run this while the server is stopped or no privacy preferences records are being saved,
    before toggling FIDES__CONSENT__CONSENT_V3_ENCRYPTION_ENABLED.
    """
    config = ctx.obj["CONFIG"]

    def progress(total: int, batch_num: int) -> None:
        click.echo(f"Processed {total} rows ({batch_num} batches)...")

    SessionLocal = get_db_session(config)
    try:
        with SessionLocal() as db:
            result = run_consent_encryption_migration(
                db,
                direction=direction,
                batch_size=batch_size,
                progress_callback=progress,
            )
    except Exception as e:
        echo_red(f"Migration failed: {e}")
        ctx.exit(1)
        return

    if result.success:
        click.echo(
            f"Done. {direction.capitalize()}ed {result.total_processed} rows "
            f"in {result.batches} batches."
        )
    else:
        echo_red(f"Completed with errors: {result.errors}")
        ctx.exit(1)
