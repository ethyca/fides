# """Contains the audit group of CLI commands for Fidesctl."""
import click

from fidesctl.cli.utils import with_analytics
from fidesctl.core import audit as _audit


@click.group(name="audit")
@click.pass_context
def audit(ctx: click.Context) -> None:
    """
    Audits fidesctl resources for compliance to build a compliant
    data map with full attribution.
    """


@audit.command(name="systems")
@click.pass_context
@with_analytics
def audit_system(
    ctx: click.Context,
) -> None:
    """
    Audits Systems for attributes that are required for a complete data map.

    Resources are validated from the server, so in work manifests are not
    considered as part of the audit.

    Findings from these audits should be evaluated by an organization and
    addressed according to the goals of the organization.
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
    Audits Organizations for attributes required for a complete data map.

    Resources are validated from the server, so in work manifests are not
    considered as part of the audit.

    Findings from these audits should be evaluated by an organization and
    addressed according to the goals of the organization.
    """
    config = ctx.obj["CONFIG"]
    _audit.audit_organizations(
        url=config.cli.server_url,
        headers=config.user.request_headers,
        exclude_keys=[],
    )
