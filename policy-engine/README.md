# policy-engine

A Go implementation of the Fides Purpose-Based Access Control (PBAC) evaluation engine, plus a standalone `fides-pbac` CLI for evaluating raw SQL queries against a PBAC config directory.

## Why this exists

The Python PBAC engine lives inside the `fides` package, which drags in FastAPI, Celery, every SaaS connector, Alembic, and the rest of the Fides framework. Any CLI that imports from `fides` inherits that startup cost (multiple seconds before emitting output).

The `fides-pbac` binary:

- Starts and loads its config in **~3 ms**.
- Is a **single 3.5 MB static binary** with one external Go dep (`gopkg.in/yaml.v3`).
- Has **no server, no database, no Redis, no Python runtime** requirement.
- Runs in CI, on a laptop, in an airgapped environment, wherever you can copy a file.

## Module layout

```
policy-engine/
├── cmd/
│   └── fides-pbac/              Standalone CLI binary (main package)
├── pkg/
│   ├── pbac/                    Purpose and policy evaluation engine
│   ├── sqlextract/              Regex-based SQL table extractor
│   └── fixtures/                YAML loaders for consumers/purposes/datasets/policies
├── go.mod
└── go.sum
```

## fides-pbac CLI

### Install from a local checkout

```bash
cd policy-engine
go install ./cmd/fides-pbac
```

`go install` builds from whatever is in your working tree (no commit or publish required). The binary lands in `$(go env GOBIN)` or `~/go/bin`. Add that to your `PATH` if it isn't already:

```bash
export PATH="$HOME/go/bin:$PATH"   # add to ~/.zshrc for persistence
```

Verify:

```bash
fides-pbac --help
```

### Fixture layout

`fides-pbac` reads a directory with this structure:

```
<config>/
├── consumers/*.yml     top-level key: consumer:
├── purposes/*.yml      top-level key: purpose:
├── datasets/*.yml      fideslang Dataset YAML, top-level key: dataset:
└── policies/*.yml      top-level key: policy:
```

Reference fixtures live at `pbac/` at the repo root, including a README describing the cast of identities, datasets, policies, and expected outcomes.

### Usage

```bash
fides-pbac --config <dir> --identity <email> [FILE]
```

If `FILE` is omitted or `-`, the CLI reads SQL from stdin. Each top-level statement (split on `;` outside strings and comments) becomes one `EvaluationRecord`. All statements in one invocation are attributed to `--identity`.

### Examples

```bash
# Against a fixture file
fides-pbac --config pbac/ \
           --identity alice@demo.example \
           pbac/entries/alice.txt

# Single query from stdin
echo "SELECT customer_id, total FROM orders" | \
  fides-pbac --config pbac/ --identity alice@demo.example -

# Pipe a batch of SQL lines
cat production-queries.sql | \
  fides-pbac --config pbac/ --identity bob@demo.example -
```

Output is JSON on stdout. The record shape mirrors `EvaluationRecord` from `src/fides/service/pbac/types.py`: one `records` array with `query_id`, `identity`, resolved `consumer`, resolved `dataset_keys`, `is_compliant`, `violations`, `gaps`, `total_accesses`, and `query_text` per SQL statement. When a policy ALLOWs a violation, the suppression is recorded inline on the violation via `suppressed_by_policy` and (when present) `suppressed_by_action`.

### Evaluation pipeline

Each SQL statement runs through:

1. **Table extraction** — `sqlextract` pulls 1-3 part qualified identifiers out of the SQL text.
2. **Identity resolution** — `--identity` looked up against `consumers/` by member email. A consumer with N members is reachable via any of them.
3. **Dataset resolution** — each extracted table is looked up in the collection-name index built from `datasets/*.yml` (`collections[].name`). Tables are assumed globally unique across datasets. Unknown tables fall through to their qualified name so the resulting gap identifies the missing table.
4. **Purpose evaluation** — consumer's `purposes` ∩ effective purposes at (dataset, collection). Effective purposes are the union of dataset `data_purposes`, collection `data_purposes`, and the union of every field's `data_purposes` in that collection. Non-overlap produces a `PurposeViolation`; missing configuration produces an `EvaluationGap`.
5. **Gap reclassification** — when the consumer exists but has no purposes, `UNRESOLVED_IDENTITY` gaps become `UNCONFIGURED_CONSUMER`.
6. **Policy filtering** — each violation's dataset purposes are mapped to their `data_use` strings via `purposes/`, then the access policy engine evaluates the loaded `policies/`. An `ALLOW` decision sets `suppressed_by_policy` (and `suppressed_by_action` when the policy has an `action.message`) on the violation, which remains in `violations` for auditability.

Gaps do not flow through policy filtering — they represent missing config, not access decisions. A record is compliant when every violation is suppressed and no gaps were recorded.

## Packages

### `pkg/pbac`

The canonical Go implementation of the Fides PBAC purpose and policy engines. Mirrors `src/fides/service/pbac/evaluate.py` and `src/fides/service/pbac/policies/evaluate.py` rule-for-rule.

Key entry points:

- `pbac.EvaluatePurpose(consumer, datasets, collections) PurposeEvaluationResult`
- `pbac.EvaluatePolicies(policies, request) *PolicyEvaluationResult`

This package has no dependencies outside the Go standard library.

### `pkg/sqlextract`

A deliberately simple regex-based extractor that pulls `TableRef{Catalog, Schema, Table}` values out of SQL text.

Handles:

- 1, 2, and 3-part qualified identifiers (`orders`, `sales.orders`, `prod.sales.orders`)
- Backtick and double-quote identifier wrapping
- Line (`--`) and block (`/* */`) comments
- Case-insensitive `FROM` / `JOIN`
- CTE names (filtered out via a `WITH ... AS (` scan)
- Subqueries (naturally skipped since `(` isn't an identifier char)
- Deduplication (case-insensitive, by qualified name)

Known limitations:

- Views are not expanded. A query that reads from a view reports the view name, not the underlying tables.
- Wildcard tables (BigQuery `events_*`) are returned verbatim.
- Tables read inside UDFs or stored procedures are missed.
- Old-style comma joins (`FROM a, b, c`) only pick up the first table.
- `FROM` tokens inside string literals (`'FROM something' AS x`) produce false positives.

For exact resolution, use the platform's audit API (BigQuery Jobs, Snowflake `ACCESS_HISTORY`, Databricks query history). sqlextract is a best-effort helper for when you only have SQL text.

### `pkg/fixtures`

YAML loaders for `consumers/`, `purposes/`, `datasets/`, and `policies/`. Returns:

- `map[member_email]Consumer` — a consumer with N members appears N times, once per member, all pointing at the same `Consumer`
- `map[fides_key]Purpose` — used to resolve dataset purposes to `data_use` strings before policy eval
- `Datasets{ Purposes, Tables }` — `Purposes` is keyed by dataset `fides_key` and fed to the engine; `Tables` is a lowercase collection-name index (`collections[].name → fides_key`) for SQL-driven dataset resolution
- `[]pbac.AccessPolicy` — disabled policies (`enabled: false`) are filtered out at load time

## What's intentionally not here

- **Column-aware extraction.** `sqlextract` pulls tables, not individual columns from SELECT lists. Field-level purposes therefore fold into their owning collection's effective set (any field's purpose broadens the whole collection). A column-aware extractor would let field-level purposes gate individual SELECTs, but that's out of scope today.
- **Runtime context for `unless` constraints.** The CLI populates `data_uses` on the policy request but not `context` (consent state, geo location, data flows). Policies that gate their ALLOW decision on consent or geo will not fire correctly until the CLI grows a way to inject that context.

## Build and test

```bash
# From policy-engine/
go build ./...
go test ./...
go vet ./...

# Build just the CLI for your platform
go build -o fides-pbac ./cmd/fides-pbac

# Cross-compile
GOOS=linux GOARCH=amd64 go build -o fides-pbac-linux-amd64 ./cmd/fides-pbac
GOOS=darwin GOARCH=arm64 go build -o fides-pbac-darwin-arm64 ./cmd/fides-pbac
GOOS=windows GOARCH=amd64 go build -o fides-pbac-windows-amd64.exe ./cmd/fides-pbac
```

Tests cover the SQL extractor (24 extraction subtests + 7 `StripComments` subtests) and the purpose / policy engines. `go vet` is clean.

## Performance

Measured on Apple Silicon, 50 warm runs per case:

| Invocation | Median | p95 |
|---|---|---|
| Empty stdin (startup + config load only) | 2.9 ms | 3.4 ms |
| Single query from stdin | 2.8 ms | 3.2 ms |
| 2-query file from disk | 2.9 ms | 3.3 ms |

The floor is process launch and Go runtime init. The engine and YAML loading are sub-millisecond.
