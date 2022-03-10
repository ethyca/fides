"""Contains reusable utils for the CLI commands."""
import asyncio
import json
import sys
from datetime import datetime, timezone
from typing import Dict

import click
import requests
from fideslog.sdk.python.client import AnalyticsClient
from fideslog.sdk.python.event import AnalyticsEvent


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


def send_analytics_event(client: AnalyticsClient, command: str) -> None:
    """
    Sends basic anonymized event information via the
    fideslog SDK.
    """
    analytics_event = AnalyticsEvent(
        event="CLI Command Executed",
        command=command,
        event_created_at=datetime.now(timezone.utc),
        status_code=200,
    )
    asyncio.run(client.send(analytics_event))
