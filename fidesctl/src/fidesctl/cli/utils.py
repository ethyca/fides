"""Contains reusable utils for the CLI commands."""
import asyncio
from datetime import datetime, timezone
from importlib.metadata import version
import json
import platform
import sys
from typing import Dict, Optional
import click
import requests
import toml

from fideslog.sdk.python import event, client


OPT_OUT_COPY = """
Fides needs your permission to send Ethyca a limited set of anonymous usage statistics.
Ethyca will only use this anonymous usage data to improve the product experience, and will never collect sensitive or personal data.

***
Don't believe us? Check out the open-source code here:
    https://github.com/ethyca/fideslog 
***

To opt-out of all telemetry, press "n". To continue with telemetry, press any other key.
"""


def pretty_echo(dict_object: Dict, color: str = "white") -> None:
    """
    Given a dict-like object and a color, pretty click echo it.
    """
    click.secho(json.dumps(dict_object, indent=2), fg=color)


def handle_cli_response(
    response: requests.Response, verbose: bool = True
) -> requests.Response:
    """Viewable CLI response"""
    if response.status_code >= 200 and response.status_code <= 299:
        if verbose:
            pretty_echo(response.json(), "green")
    else:
        try:
            pretty_echo(response.json(), "red")
        except json.JSONDecodeError:
            click.secho(response.text, fg="red")
        finally:
            sys.exit(1)
    return response


def send_anonymous_event(command: str, client_id: str) -> None:
    """
    Sends basic anonymized event information via the
    fideslog SDK.
    """
    product_name = "fidesctl"
    fideslog_client = client.AnalyticsClient(
        api_key=client_id,
        client_id=client_id,
        os=platform.system(),
        product_name=product_name,
        production_version=version(product_name),
    )
    fideslog_event = event.AnalyticsEvent(
        event=command,
        event_created_at=datetime.now(timezone.utc),
    )
    asyncio.run(fideslog_client.send(event=fideslog_event))


def opt_out_anonymous_usage(
    analytics_values: Optional[Dict] = None, config_path: str = ""
) -> bool:
    """
    This function handles the verbiage and response of opting
    in or out of anonymous usage analytic tracking.

    If opting out, return True to set the opt out config.
    """
    opt_in = input(OPT_OUT_COPY)
    if analytics_values:
        analytics_values["user"]["analytics_opt_out"] = bool(opt_in.lower() == "n")
        update_config_file(analytics_values)
    return bool(opt_in.lower() == "n")


def update_config_file(analytics_values: Dict, config_path: str = "") -> None:
    """
    Loads the current config specified by the user
    Appends any new values required to the existing config

    finally, rewrites the config file (to avoid issue duplicating sections)

    This should likely be moved to fidesctl.core.config?
    """

    config_path = config_path or ".fides/fidesctl.toml"

    current_config = toml.load(config_path)
    for key, value in analytics_values.items():
        if current_config[key]:
            current_config[key].update(value)
        else:
            current_config.update({key: value})

    with open(config_path, "w") as config_file:
        toml.dump(current_config, config_file)
