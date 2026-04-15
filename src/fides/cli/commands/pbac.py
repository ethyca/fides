"""PBAC CLI commands for the Fides privacy engineering platform.

Exposes the PBAC evaluation engine via the command line:
  fides pbac evaluate          — Full pipeline: SQL + identity + YAML fixtures
  fides pbac evaluate-purpose  — Purpose-overlap primitive (JSON in)
  fides pbac evaluate-policies — Access-policy primitive (JSON in)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TextIO

import rich_click as click

from fides.service.pbac.evaluate import evaluate_purpose
from fides.service.pbac.fixtures import load_fixtures
from fides.service.pbac.pipeline import PipelineInput, TableRef, evaluate
from fides.service.pbac.policies.evaluate import (
    InvalidPolicyError,
    evaluate_policies,
    parsed_policy_from_dict,
    request_from_dict,
    result_to_dict,
)
from fides.service.pbac.sql_parser import extract_table_refs
from fides.service.pbac.types import ConsumerPurposes, DatasetPurposes


@click.group(name="pbac")
@click.pass_context
def pbac(ctx: click.Context) -> None:
    """
    Policy-Based Access Control evaluation commands.
    """


@pbac.command(name="evaluate-purpose")
@click.argument("input_file", type=click.File("r"), default="-")
def evaluate_purpose_cmd(input_file: TextIO) -> None:
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

    try:
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
    except (TypeError, AttributeError) as e:
        click.echo(f"Error: malformed input — {e}", err=True)
        sys.exit(1)

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
def evaluate_policies_cmd(input_file: TextIO) -> None:
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
    """
    try:
        data = json.load(input_file)
    except json.JSONDecodeError as e:
        click.echo(f"Error parsing JSON: {e}", err=True)
        sys.exit(1)

    try:
        policies = [parsed_policy_from_dict(p) for p in data.get("policies", [])]
    except InvalidPolicyError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    request = request_from_dict(data.get("request", {}))
    result = evaluate_policies(policies, request)

    click.echo(json.dumps(result_to_dict(result), indent=2))


@pbac.command(name="evaluate")
@click.option(
    "--config",
    "config_dir",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help=(
        "Directory containing consumers/, purposes/, datasets/, policies/ "
        "YAML subdirectories. See pbac/ at the repo root for the layout."
    ),
)
@click.option(
    "--identity",
    required=True,
    help="Caller identity (typically email). Looked up against consumer members.",
)
@click.argument("input_file", type=click.File("r"), default="-", required=False)
def evaluate_cmd(config_dir: Path, identity: str, input_file: TextIO) -> None:
    """Run the full PBAC pipeline over SQL with YAML fixtures.

    Reads SQL from INPUT_FILE (or stdin), parses each top-level
    statement with sqlglot, extracts table references, and runs each
    statement through identity resolution -> dataset resolution ->
    purpose evaluation -> gap reclassification -> policy filtering.

    Emits a JSON object with a `records` array — one entry per statement.
    The shape mirrors `fides.service.pbac.types.EvaluationRecord` with
    two deltas: the consumer is a name string (not the full entity),
    and there is no timestamp. Violations suppressed by an ALLOW policy
    are kept in the record with `suppressed_by_policy` and the optional
    `suppressed_by_action` message attached inline.

    \b
    Example:
      fides pbac evaluate \\
        --config pbac/ \\
        --identity alice@demo.example \\
        pbac/entries/alice.txt
    """
    import sqlglot

    sql_text = input_file.read()

    try:
        fixtures = load_fixtures(config_dir)
    except Exception as e:  # noqa: BLE001 — CLI needs to surface any load error
        click.echo(f"Error loading fixtures: {e}", err=True)
        sys.exit(1)

    try:
        statements = sqlglot.parse(sql_text)
    except Exception as e:  # noqa: BLE001
        click.echo(f"Error parsing SQL: {e}", err=True)
        sys.exit(1)

    records = []
    for idx, stmt in enumerate(statements):
        if stmt is None:
            continue
        stmt_text = stmt.sql()
        table_refs = tuple(
            TableRef(
                collection=t.name,
                qualified_name=_qualified_name(t.catalog, t.db, t.name),
            )
            for t in stmt.find_all(sqlglot.expressions.Table)
            if t.name
        )
        record = evaluate(
            fixtures,
            PipelineInput(
                query_id=f"q{idx + 1}",
                identity=identity,
                query_text=stmt_text,
                tables=table_refs,
            ),
        )
        records.append(record.to_dict())

    click.echo(json.dumps({"records": records}, indent=2))


def _qualified_name(catalog: str, schema: str, table: str) -> str:
    """Join a (catalog, schema, table) triple into `a.b.c`, skipping empties."""
    return ".".join(part for part in (catalog, schema, table) if part)
