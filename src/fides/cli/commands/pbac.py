"""PBAC CLI commands for the Fides privacy engineering platform.

All evaluation logic runs in Go via the libpbac shared library.
Python handles only:
  - CLI argument parsing (click)
  - SQL parsing (sqlglot)
  - JSON I/O

Commands:
  fides pbac evaluate          — Full pipeline: YAML fixtures + SQL + identity
  fides pbac evaluate-purpose  — Purpose-overlap primitive (JSON in)
  fides pbac evaluate-policies — Access-policy primitive (JSON in)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TextIO

import rich_click as click

from fides.service.pbac.engine import (
    evaluate_pipeline,
    evaluate_policies,
    evaluate_purpose,
    load_fixtures,
)


@click.group(name="pbac")
@click.pass_context
def pbac(ctx: click.Context) -> None:
    """
    Policy-Based Access Control evaluation commands.
    """


# ── Full pipeline ────────────────────────────────────────────────────


@pbac.command(name="evaluate")
@click.option(
    "--config",
    "config_dir",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help=(
        "Directory containing consumers/, purposes/, datasets/, policies/ "
        "YAML subdirectories."
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

    Reads SQL from INPUT_FILE (or stdin), parses each statement with
    sqlglot, extracts table references, and runs the full pipeline
    (identity resolution, dataset resolution, purpose evaluation, gap
    reclassification, policy filtering) via the Go evaluation library.

    \b
    Example:
      fides pbac evaluate \\
        --config pbac/ \\
        --identity alice@demo.example \\
        pbac/entries/alice.txt
    """
    import sqlglot
    import sqlglot.expressions as exp

    sql_text = input_file.read()

    try:
        fixtures = load_fixtures(config_dir)
    except RuntimeError as e:
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
        tables = [
            {
                "collection": t.name,
                "qualified_name": _qualified_name(t.catalog, t.db, t.name),
            }
            for t in stmt.find_all(exp.Table)
            if t.name
        ]
        record = evaluate_pipeline(
            fixtures,
            {
                "query_id": f"q{idx + 1}",
                "identity": identity,
                "query_text": stmt_text,
                "tables": tables,
            },
        )
        records.append(record)

    click.echo(json.dumps({"records": records}, indent=2))


# ── Lower-level primitives ───────────────────────────────────────────


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

    result = evaluate_purpose(
        consumer=data.get("consumer", {}),
        datasets=data.get("datasets", {}),
        collections=data.get("collections"),
    )

    click.echo(json.dumps(result, indent=2))


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
          "unless": [...],
          "action": {"message": "..."}
        }
      ],
      "request": {
        "data_uses": ["marketing.advertising"],
        "data_categories": ["user.contact.email"],
        "context": {"consent": {"do_not_sell": "opt_out"}}
      }
    }
    """
    try:
        data = json.load(input_file)
    except json.JSONDecodeError as e:
        click.echo(f"Error parsing JSON: {e}", err=True)
        sys.exit(1)

    result = evaluate_policies(
        policies=data.get("policies", []),
        request=data.get("request", {}),
    )

    click.echo(json.dumps(result, indent=2))


def _qualified_name(catalog: str, schema: str, table: str) -> str:
    """Join a (catalog, schema, table) triple, skipping empties."""
    return ".".join(part for part in (catalog, schema, table) if part)
