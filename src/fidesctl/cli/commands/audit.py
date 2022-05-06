# """Contains the audit group of CLI commands for Fidesctl."""
import click

from fidesctl.cli.utils import with_analytics
from fidesctl.core import audit as _audit


@click.group(name="audit")
@click.pass_context
def audit(ctx: click.Context) -> None:
    """
    Audit fidesctl resources for compliance
    """


@audit.command(name="systems")
@click.pass_context
@with_analytics
def audit_system(
    ctx: click.Context,
) -> None:
    """
    Audit Systems for attributes that are required for a complete data map.
    """
    config = ctx.obj["CONFIG"]
    _audit.audit_systems(
        url=config.cli.server_url,
        headers=config.user.request_headers,
        exclude_keys=[],
    )


@audit.command(name="organizations")
@click.pass_context
@with_analytics
def audit_organizations(
    ctx: click.Context,
) -> None:
    """
    Audit Organizations for attributes required for a complete data map.
    """
    config = ctx.obj["CONFIG"]
    _audit.audit_organizations(
        url=config.cli.server_url,
        headers=config.user.request_headers,
        exclude_keys=[],
    )
