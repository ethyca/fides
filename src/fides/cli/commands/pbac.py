"""PBAC CLI commands for the Fides privacy engineering platform.

Exposes the PBAC evaluation engine via the command line:
  fides pbac evaluate-purpose  — Check consumer/dataset purpose overlap
  fides pbac evaluate-policies — Run access policies against a violation
"""

from __future__ import annotations

import json
import sys

import rich_click as click

from fides.service.pbac.evaluate import evaluate_purpose
from fides.service.pbac.types import ConsumerPurposes, DatasetPurposes


@click.group(name="pbac")
@click.pass_context
def pbac(ctx: click.Context) -> None:
    """
    Policy-Based Access Control evaluation commands.
    """


@pbac.command(name="evaluate-purpose")
@click.argument("input_file", type=click.File("r"), default="-")
def evaluate_purpose_cmd(input_file: click.utils.LazyFile) -> None:
    """Evaluate purpose overlap between a consumer and datasets.

    Reads JSON from INPUT_FILE (or stdin if omitted).

    \b
    Expected JSON schema:
    {
      "consumer": {
        "consumer_id": "...",
        "consumer_name": "...",
        "purpose_keys": ["billing", "analytics"]
      },
      "datasets": {
        "dataset_key": {
          "dataset_key": "...",
          "purpose_keys": ["billing"],
          "collection_purposes": {"collection_name": ["purpose1"]}
        }
      },
      "collections": {"dataset_key": ["collection1", "collection2"]}
    }
    """
    try:
        data = json.load(input_file)
    except json.JSONDecodeError as e:
        click.echo(f"Error parsing JSON: {e}", err=True)
        sys.exit(1)

    consumer_data = data.get("consumer", {})
    consumer = ConsumerPurposes(
        consumer_id=consumer_data.get("consumer_id", ""),
        consumer_name=consumer_data.get("consumer_name", ""),
        purpose_keys=frozenset(consumer_data.get("purpose_keys", [])),
    )

    datasets: dict[str, DatasetPurposes] = {}
    for key, ds_data in data.get("datasets", {}).items():
        collection_purposes = {
            col: frozenset(purposes)
            for col, purposes in ds_data.get("collection_purposes", {}).items()
        }
        datasets[key] = DatasetPurposes(
            dataset_key=ds_data.get("dataset_key", key),
            purpose_keys=frozenset(ds_data.get("purpose_keys", [])),
            collection_purposes=collection_purposes,
        )

    collections_raw = data.get("collections", {})
    collections: dict[str, tuple[str, ...]] | None = (
        {k: tuple(v) for k, v in collections_raw.items()} if collections_raw else None
    )

    result = evaluate_purpose(consumer, datasets, collections=collections)

    output = {
        "violations": [
            {
                "consumer_id": v.consumer_id,
                "consumer_name": v.consumer_name,
                "dataset_key": v.dataset_key,
                "collection": v.collection,
                "consumer_purposes": sorted(v.consumer_purposes),
                "dataset_purposes": sorted(v.dataset_purposes),
                "reason": v.reason,
            }
            for v in result.violations
        ],
        "gaps": [
            {
                "gap_type": g.gap_type.value,
                "identifier": g.identifier,
                "dataset_key": g.dataset_key,
                "reason": g.reason,
            }
            for g in result.gaps
        ],
        "total_accesses": result.total_accesses,
    }

    click.echo(json.dumps(output, indent=2))


@pbac.command(name="evaluate-policies")
@click.argument("input_file", type=click.File("r"), default="-")
def evaluate_policies_cmd(input_file: click.utils.LazyFile) -> None:
    """Evaluate access policies against a PBAC violation.

    Reads JSON from INPUT_FILE (or stdin if omitted).

    \b
    Expected JSON schema:
    {
      "policies": [
        {
          "key": "allow-marketing",
          "priority": 100,
          "enabled": true,
          "decision": "ALLOW",
          "match": {"data_use": {"any": ["marketing"]}},
          "unless": [{"type": "consent", "privacy_notice_key": "...", "requirement": "opt_out"}],
          "action": {"message": "..."}
        }
      ],
      "request": {
        "consumer_id": "...",
        "consumer_name": "...",
        "data_uses": ["marketing.advertising"],
        "data_categories": ["user.contact.email"],
        "data_subjects": ["customer"],
        "context": {"consent": {"do_not_sell": "opt_out"}}
      }
    }

    \b
    This is the same evaluation the Go sidecar performs at API speed.
    The CLI runs it through Python for convenience — use the sidecar
    for production throughput.
    """
    try:
        data = json.load(input_file)
    except json.JSONDecodeError as e:
        click.echo(f"Error parsing JSON: {e}", err=True)
        sys.exit(1)

    from fides.service.pbac.policies.evaluate import evaluate_access_policies

    policies = data.get("policies", [])
    request = data.get("request", {})

    result = evaluate_access_policies(policies, request)

    click.echo(json.dumps(result, indent=2))
