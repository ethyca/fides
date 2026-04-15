# PBAC demo fixtures

Sample data for the `fides-pbac` CLI (Go standalone binary, see
`policy-engine/README.md`). Each `.txt` file in `entries/` is one
identity's SQL queries; the CLI is told which identity via
`--identity`, extracts table references from the SQL with
`pkg/sqlextract`, and runs them through the full PBAC pipeline
(purpose evaluation + policy filtering).

All domains use RFC 2606 reserved `.example` suffixes so this is safe
to commit to the public repo.

## Cast

| Identity | Consumer | Purposes |
|---|---|---|
| `alice@demo.example`, `priya@demo.example` | Analytics Team | `analytics` |
| `bob@demo.example`, `maria@demo.example` | Marketing Team | `marketing` |
| `dave@demo.example` | Onboarding | *none declared* |
| `carol@demo.example` | *not registered* | |

| Purpose | `data_use` |
|---|---|
| `analytics` | `analytics.reporting` |
| `marketing` | `marketing.advertising` |
| `billing` | `essential.service.payment_processing` |

| Dataset (`fides_key`) | Dataset `data_purposes` | Collections |
|---|---|---|
| `sales` | `billing` | `orders`, `invoices` (+ `analytics` at collection level) |
| `events` | `analytics` | `page_views` |
| `marketing` | `marketing` | `campaigns` |

Tables are assumed to be **globally unique across datasets**, so the CLI
resolves queries by bare table name. `SELECT ... FROM orders` and
`SELECT ... FROM warehouse.archive.orders` both resolve to whichever
dataset declares an `orders` collection. A query naming a table that
isn't a declared collection (e.g. `cold_storage`) produces an
`UNCONFIGURED_DATASET` gap identified by the query's qualified name.

## Purposes at three levels

`data_purposes` can appear on the dataset, each collection, and each
field. They stack additively:

```
effective_purposes(dataset.collection)
  = dataset.data_purposes
  ∪ collection.data_purposes
  ∪ union(field.data_purposes for each field in collection)
```

The engine currently evaluates at collection granularity (the CLI
extracts tables, not individual columns from SELECT lists), so
field-level purposes fold into their owning collection's effective
set. A column-aware extractor would let field-level purposes gate
individual SELECTs, but that's out of scope today.

`sales.invoices` demonstrates the collection layer: the dataset is
`billing`, the collection adds `analytics`, so analytics-team queries
against invoices pass the purpose check at the engine without needing
any policy override.

## Access policies

`policies/allow-analytics-on-billing-data.yml` shows a realistic ALLOW
override. It matches any violation where the dataset's purposes resolve
to `essential.service.payment_processing` (the `billing` purpose's
`data_use`) and suppresses the violation.

Policy evaluation only runs on purpose violations. Compliant queries
and coverage gaps pass through unchanged — gaps represent missing
configuration, not access decisions.

## File layout

```
pbac/
  consumers/   one YAML per consumer  (top-level key: consumer:)
  purposes/    one YAML per purpose   (top-level key: purpose:)
  datasets/    fideslang Dataset YAML (top-level key: dataset:)
  policies/    one YAML per policy    (top-level key: policy:)
  entries/     one .txt per identity, raw SQL separated by semicolons
```

## Invocation

```bash
fides-pbac --config pbac/ --identity alice@demo.example pbac/entries/alice.txt
fides-pbac --config pbac/ --identity bob@demo.example   pbac/entries/bob.txt
fides-pbac --config pbac/ --identity carol@demo.example pbac/entries/carol.txt
fides-pbac --config pbac/ --identity dave@demo.example  pbac/entries/dave.txt
```

## Expected outcomes

| File | Query | Outcome |
|---|---|---|
| `alice.txt` | `SELECT ... FROM page_views ...` | **compliant** (analytics ∩ analytics) |
| `alice.txt` | `SELECT ... FROM orders ...` | violation **suppressed** by `allow-analytics-on-billing-data` |
| `alice.txt` | `SELECT ... FROM invoices ...` | **compliant** via collection-level `analytics` on `sales.invoices` |
| `alice.txt` | `SELECT ... FROM campaigns ...` | **violation stands** — no matching policy |
| `bob.txt` | `SELECT ... FROM cold_storage ...` | **gap** `UNCONFIGURED_DATASET` |
| `carol.txt` | `SELECT ... FROM page_views` | **gap** `UNRESOLVED_IDENTITY` |
| `dave.txt` | `SELECT ... FROM page_views ...` | **gap** `UNCONFIGURED_CONSUMER` |

## Schema notes

**Consumer YAML**. A consumer represents a group (or individual) that
accesses data, with a list of identities under `members`. Every member
email resolves to the same consumer, so an identity match in the CLI is
"`identity` appears in some consumer's `members` list."

```yaml
consumer:
- name: Analytics Team
  members:
  - alice@demo.example
  - priya@demo.example
  purposes: [analytics]
```

If the same identity appears in multiple consumers, the last one loaded
wins.

**Purpose YAML** mirrors `fidesplus/seed/pbac/data.py::PURPOSES`:

```yaml
purpose:
- fides_key: analytics
  name: Product Analytics
  data_use: analytics.reporting
  data_categories: [user.behavior]
```

**Dataset YAML** is standard fideslang. `data_purposes` can be declared
at the dataset, collection, and field levels; they stack additively
(see "Purposes at three levels" above). `sales.invoices` demonstrates
the collection layer — `sales` is `billing` at the dataset level,
`invoices` adds `analytics` at the collection level, so analytics-team
queries against `invoices` pass the purpose check directly.

**Policy YAML** matches `pbac.AccessPolicy`:

```yaml
policy:
- key: allow-analytics-on-billing-data
  priority: 100
  enabled: true
  decision: ALLOW
  match:
    data_use:
      any:
      - essential.service.payment_processing
  unless: []
  action:
    message: ...
```

Match blocks key on the `data_use` of the dataset being accessed
(the CLI resolves dataset purposes to their `data_use` via the
purposes/ directory before calling the policy engine).
