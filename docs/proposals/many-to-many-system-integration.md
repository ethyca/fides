# Proposal: Many:Many System-to-Integration Relationship

**Status:** Draft / Analysis
**Ticket:** ENG-2799
**Author:** asachs
**Date:** 2026-03-04

## Background

PR #7432 introduced a `system_connection_config_link` join table to decouple
systems and integrations. The current constraints enforce:

- **Many:one** (many integrations per system) — landed in PR #7555
- **One:one** on the reverse side — each integration belongs to at most one
  system, enforced by a `UNIQUE` constraint on `connection_config_id`

This document analyzes what it would take to lift the unique constraint and
support **many:many**: a single integration shared across multiple systems.

---

## Database Changes

### Migration

Drop the unique index on `connection_config_id` and replace it with a
composite unique on `(system_id, connection_config_id)` to prevent duplicate
links while allowing the same integration to appear in multiple systems:

```sql
DROP INDEX ix_system_connection_config_link_connection_config_id;

CREATE INDEX ix_system_connection_config_link_connection_config_id
  ON system_connection_config_link(connection_config_id);

CREATE UNIQUE INDEX uq_system_connection_config_link
  ON system_connection_config_link(system_id, connection_config_id);
```

### Model

`SystemConnectionConfigLink.connection_config_id` — remove `unique=True`.

### ORM Relationship

`ConnectionConfig.system` (`uselist=False`) becomes
`ConnectionConfig.systems` (`uselist=True`).

### Repository

`create_or_update_link()` currently deletes _all_ existing links for a
connection config before inserting, enforcing "replace" semantics. For M:M
this must split into `add_link()` (idempotent insert) and `remove_link()`
(targeted delete).

---

## Callsite Inventory

18 locations across fides + fidesplus access `connection_config.system` as a
scalar. They fall into three categories:

### Category A: Core Logic (consent, data use filtering)

| File | Lines | What it does |
|------|-------|-------------|
| `connectionconfig.py` | 257 | `system = relationship(..., uselist=False)` |
| `connectionconfig.py` | 280-287 | `system_key` property returns `self.system.fides_key` |
| `saas_connector.py` | 752, 803 | Passes `self.configuration.system` to consent filtering |
| `consent_email_connector.py` | 163, 235 | Passes `self.configuration.system` to consent filtering |
| `create_request_tasks.py` | 68-76 | Resolves data uses from `connection_config.system` |
| `request_runner_service.py` | 130 | `manual_webhook.connection_config.system.name` |
| `datastore_discovery_monitor.py` (fidesplus) | 92 | `self.system = self.connection_config.system` |

### Category B: API / Schema / Display

| File | Lines | What it does |
|------|-------|-------------|
| `connection_config.py` (schema) | 127-137 | Populates `linked_systems` list in API response |
| `oauth_endpoints.py` | 304-308 | OAuth callback redirect to system page |
| `dataset_service.py` | 89-99 | Display string: "in system 'X'" |
| `saas_connector.py` | 83-91 | Log context: `system_key` for structured logging |

### Category C: Already Compatible / Easy

| File | Lines | What it does |
|------|-------|-------------|
| `system.py` endpoint | 118-125 | Queries through join table (no change needed) |
| `repository.py` | 20-28 | Eager loading (returns more rows, works as-is) |
| `repository.py` | 84-113 | `create_or_update_link` (needs split, see above) |
| `manual_webhook.py` | 141-157 | `selectinload(ConnectionConfig.system)` |

---

## Deep-Dive: The Three Hard Questions

### 1. Consent Filtering: Can We Union Data Uses Across Systems?

**How it works today:**

`filter_privacy_preferences_for_propagation(system, preferences)` filters
privacy preferences down to those whose notice data uses overlap with the
system's declared data uses. This is called once per connector, with the
single linked system.

The key method is `PrivacyNotice.applies_to_system(system)`:

```python
def applies_to_system(self, system: System) -> bool:
    for system_data_use in System.get_data_uses([system], include_parents=True):
        for privacy_notice_data_use in self.data_uses or []:
            if system_data_use == privacy_notice_data_use:
                return True
    return False
```

**What breaks if we union:**

Unioning data uses from multiple systems _widens the filter_, meaning more
preferences match each connector. This is semantically wrong because it
conflates consent decisions that were system-specific:

- **Over-propagation:** System A declares `marketing.advertising`, System B
  declares `analytics.reporting`. A user who opted out of `marketing` would
  have that opt-out propagated to the connector even when it's acting on
  behalf of System B (which has nothing to do with marketing).

- **Conflict resolution breaks:** The global consent workflow resolves
  conflicts by preferring opt-out. With unioned data uses, a marketing
  opt-out from System A and an analytics opt-in from System B both appear
  "relevant" to the same connector. The opt-out wins, suppressing the
  analytics opt-in that should have been propagated.

- **`None` system already skips filtering:** When a connector has no linked
  system, the function returns _all_ propagatable preferences unfiltered.
  Unioning multiple systems is strictly less bad than `None`, but still
  loses per-system granularity.

**Recommendation:**

Do **not** union data uses. Instead, propagate consent _per linked system_.
When a connector is linked to systems A and B, run the consent flow twice:
once with System A's data uses, once with System B's. This preserves
per-system consent semantics. The consent tracking key (from PR #7557)
already supports per-connection keying, but would need extension to
per-connection-per-system if the same connector can serve multiple systems.

This is the most complex part of the M:M work and needs its own design doc
if pursued.

### 2. Data Use Resolution in `create_request_tasks.py`: Does It Matter?

**What it does:**

`format_data_use_map_for_caching()` builds a `Dict[str, Set[str]]` mapping
each collection address to the data uses declared by its connection's linked
system. This map is cached in Redis before request execution begins.

**How it's consumed:**

The map is passed through `privacy_request.cache_data_use_map()` and later
retrieved via `privacy_request.get_cached_data_use_map()`, which feeds into
the `upload()` function in `storage_uploader_service.py`.

**The key finding: this is effectively dead code.**

The `upload()` function accepts `data_use_map` as a parameter but **never
passes it** to any of the underlying uploader implementations (`_s3_uploader`,
`_local_uploader`, `_gcs_uploader`). The `DSRReportBuilder`, JSON encryption,
and CSV generation paths also do not consume it.

Access request _filtering_ is done by **data categories** (via
`filter_data_categories()` in `filter_results.py`), not data uses. The data
use map appears to have been scaffolded for future use in DSR output packages
but was never wired up.

**Impact of unioning data uses from multiple systems:** Effectively zero for
current behavior. The cached map would contain a superset of data uses per
collection, but since nothing reads those values, it changes no outcomes.

**Recommendation:**

Unioning is safe here — or we could skip the caching entirely for M:M
connectors. If this code is ever activated for DSR output packages, the union
approach is actually correct: the output should reflect all data uses that
apply to the collection's data.

### 3. Redirect Paths: Do They Need a Single System?

**The only redirect is the OAuth callback:**

```python
# oauth_endpoints.py, lines 304-308
if connection_config.system is not None:
    system_key = connection_config.system.fides_key
    redirect_path = f"/systems/configure/{system_key}"
else:
    redirect_path = f"/integrations/{connection_config.key}"
```

After a user completes an OAuth flow (e.g., authorizing a SaaS connector),
this redirects them back to the system configuration page or integration
detail page, with a `?status=succeeded|failed|skipped` query parameter.

**What happens with multiple systems:**

The OAuth flow is authorizing the _connection_, not a system. The redirect
is a UX convenience to put the user back where they started. With M:M:

- **Option A: Redirect to the integration page.** Always redirect to
  `/integrations/{connection_key}` regardless of system links. This is the
  simplest fix and arguably more correct — the user just authorized the
  _integration_, so show them the integration page.

- **Option B: Redirect to the "primary" system.** If we add a `primary`
  flag or use first-linked ordering on the join table, redirect to that
  system. This preserves the current UX for the common case.

- **Option C: Interstitial page.** Show a disambiguation page listing the
  linked systems. This is over-engineered for an edge case (M:M + OAuth
  is rare).

**Recommendation:** Option A. The fallback path
(`/integrations/{connection_key}`) already exists and works. Simplify the
redirect to always use the integration page when multiple systems are linked.

**Other display uses of `connection_config.system.name`:**

- `request_runner_service.py` (manual webhook): Stores `system_name` in
  webhook response data for display. With M:M, could join system names
  (e.g., `"System A, System B"`) or use the primary system.

- `dataset_service.py`: Error message "in system 'X'" when preventing
  dataset deletion. Could list all linked systems or use first.

- `saas_connector.py` log context: Structured log field `system_key`. Could
  log as a list or use first.

None of these are blocking — they're display/logging concerns with simple
fallbacks.

---

## Summary: Effort Estimate by Area

| Area | Effort | Notes |
|------|--------|-------|
| Migration + model | Small | Drop unique, add composite unique |
| ORM relationship | Small | `uselist=True`, rename to `systems` |
| Repository | Small | Split `create_or_update_link` |
| Schema / API response | Small | `linked_systems` already a list |
| OAuth redirect | Small | Always redirect to integration page |
| Display strings | Small | Join names or use first |
| Data use caching | None | Dead code, union is safe |
| **Consent propagation** | **Large** | Needs per-system-per-connection flow; separate design |
| **Discovery monitor** (fidesplus) | Medium | Needs to handle multiple systems |
| Tests | Medium | Update all `connection_config.system` assertions |

**Bottom line:** The M:M database/API/display changes are straightforward.
The blocker is **consent propagation semantics** — running consent per linked
system instead of per connector requires rethinking the consent flow and
tracking model. This should be scoped as a separate effort with its own
design doc.

---

## Risks

1. **Consent correctness** — Getting consent propagation wrong has compliance
   implications. The per-system-per-connection consent model needs careful
   design and review.

2. **API breaking change** — `connection_config.system` (singular) in any
   public-facing API responses would become a list. External consumers would
   break.

3. **Performance** — Eager loading `ConnectionConfig.systems` adds JOINs.
   With `lazy="selectin"` this should be manageable but needs benchmarking
   on large deployments.

4. **Migration of existing data** — No data migration needed (existing rows
   stay as-is), but the behavioral change means a connector previously
   linked to 1 system could now be linked to N systems by users.
