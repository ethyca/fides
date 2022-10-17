"""Defines the CLI commands for the System Scanner"""

from os import path
from subprocess import DEVNULL, CalledProcessError, run
from typing import Any, Callable, Tuple

from click import Context, echo, group, option, pass_context

from ...ctl.core.utils import echo_red
from ..options import dry_flag, verbose_flag, yes_flag
from ..utils import with_analytics

RESERVED_LABELS = [
    "app",
    "component",
    "vizier-bootstrap",
    "vizier-updater-dep",
]


def with_px_auth(func: Callable) -> Callable:
    def wrapper(ctx: Context, *args, **kwargs) -> Any:  # type: ignore
        if "system_scanner" not in ctx.obj["CONFIG"]:
            echo_red("System scanner configuration not found")
            raise SystemExit(1)

        if "pixie_api_key" not in ctx.obj["CONFIG"].system_scanner:
            echo_red("System scanner API key not found")
            raise SystemExit(1)

        try:
            run(
                [
                    "px auth login",
                    f"--api_key={ctx.obj['CONFIG'].system_scanner.pixie_api_key}",
                    "--quiet",
                ],
                check=True,
            )
        except (CalledProcessError, FileNotFoundError):
            echo_red("Authentication failed")
            raise SystemExit(1)

        return func(*args, **kwargs)

    return wrapper


def validate_labels(labels: Tuple) -> None:
    for label in labels:
        label_str = label.split("=")[0]
        if label_str in RESERVED_LABELS:
            echo(f"Supplied a reserved label string: {label_str}")
            echo("See -h, --help output for a list of reserved label strings.")
            raise ValueError


@group(name="system_scanner")
@pass_context
def system_scanner(ctx: Context) -> None:
    """
    Commands to use and manage the System Scanner. Requires fidesctl-plus.
    """


@system_scanner.command(name="deploy")
@pass_context
@option(
    "--annotation",
    "-a",
    help=(
        "Custom annotation to apply to the deployed resources, in key=value format. "
        + "This option may be included multiple times; once for each desired annotation."
    ),
    multiple=True,
)
@option(
    "--cluster-name",
    "-c",
    "cluster_name",
    help="The name of your cluster. Otherwise, the name will be taken from the current kubeconfig.",
    type=str,
)
@option(
    "--deploy-olm",
    "-o",
    is_flag=True,
    help=(
        "Whether to deploy Operator Lifecycle Management (OLM). OLM is required. "
        + "Omit this argument only if OLM has already been deployed on the cluster manually, or through another application. "
        + "OLM is deployed by default on Openshift clusters."
    ),
)
@dry_flag
@option(
    "--kubeconfig",
    "-k",
    "kubeconfig_path",
    help=(
        "Absolute path to the kubeconfig file. "
        # Intentionally not a `click` default value, to prevent populating it when left unset by the user.
        + f"[default: {path.expanduser('~')}/.kube/config]"
    ),
    show_default=True,
    type=str,
)
@option(
    "--label",
    "-l",
    help=(
        "Custom label to apply to the deployed resources, in key=value format. "
        + "This option may be included multiple times; once for each desired label. "
        + f"The following labels are reserved for internal use, and may not be used: {', '.join(RESERVED_LABELS)}."
    ),
    multiple=True,
)
@option(
    "--use-etcd-operator",
    "-e",
    is_flag=True,
    help=(
        "Whether to use the operator for etcd instead of the statefulset. "
        + "Required for clusters that do not support persistent volumes."
    ),
)
@verbose_flag
@yes_flag
@with_px_auth
@with_analytics
def system_scanner_deploy(
    ctx: Context,
    annotation: Tuple,
    label: Tuple,
    cluster_name: str = "",
    deploy_olm: bool = False,
    dry: bool = False,
    kubeconfig_path: str = "",
    use_etcd_operator: bool = False,
    verbose: bool = False,
    yes: bool = False,
) -> None:
    """
    Deploy the required pods to a Kubernetes cluster.
    """

    try:
        annotations = ""
        if len(annotation):
            annotations = "--annotations=" + ",".join(annotation)

        labels = ""
        if len(label):
            validate_labels(label)
            labels = "--labels=" + ",".join(label)

        args = [
            annotations,
            "--check_only" if dry else "",
            f'--cluster_name="{cluster_name}"' if cluster_name else "",
            "--deploy_olm" if deploy_olm else "",
            f'--kubeconfig="{kubeconfig_path}"' if kubeconfig_path else "",
            labels,
            "--olm_namespace fides-olm",
            "--olm_operator_namespace fides-operator",
            "" if verbose else "--quiet",
            "--use_etcd_operator" if use_etcd_operator else "",
            "-y" if yes else "",
        ]
        deploy_cmd = ["px deploy"] + [arg for arg in args if arg]

        run(deploy_cmd, check=True, shell=True, stderr=DEVNULL)
    except (CalledProcessError, FileNotFoundError, ValueError):
        echo_red("Pod deployment failed")
        raise SystemExit(1)
