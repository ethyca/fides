"""Contains reusable utils for the CLI commands."""
import asyncio
import json
import platform
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from typing import Dict

import click
import requests
from fideslog.sdk.python import client, event


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
        client_id=client_id,
        os=platform.system(),
        product_name=product_name,
        production_version=version(product_name),
    )
    fideslog_event = event.AnalyticsEvent(
        event="CLI",
        command=command,
        event_created_at=datetime.now(timezone.utc),
        status_code=200,
    )
    asyncio.run(fideslog_client.send(event=fideslog_event))
