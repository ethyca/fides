"""Defines the CLI commands for the System Scanner"""

from click import Context, group, pass_context

from ..options import dry_flag, verbose_flag
from ..utils import with_analytics


@group(name="system_scanner")
@pass_context
def system_scanner(ctx: Context) -> None:
    """
    Commands to use and manage the System Scanner. Requires fidesctl-plus.
    """


@system_scanner.command(name="deploy")
@pass_context
@verbose_flag
@dry_flag
@with_analytics
def system_scanner_deploy(
    ctx: Context,
    verbose: bool = False,
    dry: bool = False,
) -> None:
    """
    Deploy the required pods to the configured Kubernetes cluster.
    """
