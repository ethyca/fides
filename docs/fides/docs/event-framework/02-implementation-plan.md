# Event Framework — Implementation Plan

Phasing for the rollout of the event framework described in `01-design.md`. Each phase is independently shippable. Phase 1 is a hard prerequisite for 2 and 3; Phases 2 and 3 are independent of each other and may be sequenced by team availability.

## Phase 1 — Framework Plumbing (fides OSS)

Land the framework with no consumers. Validate end-to-end with a unit-level "ping" event used in tests.

### Scope

- New `fides.api.events` package containing:
  - `publish_after_commit(session, event)` — registers an `after_commit` callback on the session.
  - `@subscribes_to(EventType, queue="fides")` — decorator that registers a handler in the in-process registry and binds a Celery task wrapper.
  - `@publishes(EventType, ...)` — repository/service method marker for documentation, static registry, and test-time enforcement.
  - Dispatcher: walks the registry on commit, generates `event_id`, calls `celery.send_task` per (event, subscriber).
  - Registry: `dict[type[Event], list[Subscriber]]` populated by autodiscovery.
  - Serialization: dataclass → dict for Celery payloads; dict → dataclass on the worker side.
- Celery integration:
  - Task wrappers around subscriber callables, registered with the existing Celery app.
  - `event_id` propagation through `before_task_publish` / `task_prerun` / `task_postrun` signals (mirrors the existing `request_id` pattern in `fides/api/tasks/__init__.py`).
- Logging:
  - Publish, dispatch, handle log lines, structured per `01-design.md` §8.
- Subscriber autodiscovery:
  - Hook into the existing `autodiscover_task_locations` pattern. Subscribers are picked up the same way Celery tasks are.
- Test helpers (in `tests/...` under fides):
  - `assert_event_published(session, EventType)` for unit-level publish assertions.
  - Marker-coverage test: every `@publishes(EventType)` method calls `publish_after_commit` for that type.
  - Registry-coverage test: every event type has ≥ 1 publisher; every subscriber's event type has ≥ 1 publisher in tree.
- Documentation:
  - This plan + the design doc published.
  - In-repo how-to (likely `dev-docs/events.md` or similar) showing the canonical publish + subscribe + reconciler example.

### Validation

A "ping" event lives only in tests. A test publishes it from inside a transactional context, commits, and asserts a corresponding Celery task was dispatched and ran. Also covers the rollback case (no dispatch).

### Out of scope

- Any actual event types, publishers, or subscribers in production code.
- Metrics emission (logging-only for v1).
- Operator-facing tooling (e.g. event replay) — the reconciler model intentionally substitutes.

### Acceptance criteria

- Unit + integration tests passing in fides repo.
- Marker- and registry-coverage tests in place and green.
- Design and how-to docs merged.
- No subscribers or publishers in production code paths.

## Phase 2 — Monitor Stewardship Inheritance

Driving use case 1 from `01-design.md` §3.1. Splits across both repos: events emitted from fides (where `System.data_stewards` and `system_connection_config_link` live), subscriber + reconciler in fidesplus.

### fides changes

- Define event types in `fides.api.events.system_events`:
  - `SystemDataStewardsChanged(system_id: str)`
  - `SystemConnectionLinkChanged(system_id: str, connection_config_id: str, change: Literal["added", "removed"])`
  - Additional events as needed for full trigger coverage.
- Apply the recommended publish-from-repository pattern (`01-design.md` §6.6) to System-stewardship mutation paths. Where a repository method does not yet exist for a mutation site, introduce one as a targeted refactor — only the methods that mutate `systemmanager` membership and `system_connection_config_link` rows. This is a recommended pattern for these use cases, not a framework requirement.
- Add `publish_after_commit` calls (and optionally `@publishes(...)` markers per §6.5) on those methods.
- Tests: extend coverage so each new publish path has a unit-level assertion.

### fidesplus changes

- Define monitor-side event types where needed: e.g. `MonitorInheritanceFlagChanged(monitor_config_id: str, enabled: bool)`. Emit from the monitor config update repository / service.
- Build the inheritance subscriber:
  - Handler function decorated `@subscribes_to(SystemDataStewardsChanged)` and any other relevant event types.
  - Reads current state via existing repositories: list inheriting monitors for the system, compute desired inherited steward set, reconcile `monitorsteward` rows (add missing, delete now-stale, leave explicit untouched).
  - Lives under the discovery monitor service area (`fidesplus/api/service/discovery/...` or a new `monitor_stewards/` package — TBD during implementation).
- Build the reconciler:
  - APScheduler job: full sweep over every `MonitorConfig` with `inherit_system_stewards = TRUE`, running the same reconcile logic regardless of whether events fired.
  - On-demand API endpoint to trigger immediately. Auth: requires existing monitor-steward write scope.
  - Cadence: starting at 15-30 minutes, configurable via `DetectionDiscoverySettings`. Tighter than a typical reconciler because functional staleness (not just display staleness) is at stake — until propagation runs, inherited stewardship is not in effect. Confirm with product (open question §10.2 of design doc).
- Backfill on rollout:
  - One-off task that runs the reconciler at deploy time for any monitor with `inherit_system_stewards = TRUE` that has never been reconciled.

### Tests

- fides: publish-path unit tests on each new repository method.
- fidesplus: subscriber tests (happy path, no-op when nothing changed, monitor not inheriting, multiple linked systems).
- fidesplus: reconciler tests, including the case where events stopped flowing entirely — the reconciler must produce the correct end state.

### Acceptance criteria

- Subscriber + reconciler converge on identical end state for a battery of seeded scenarios.
- Reconciler handles tenant-scale data without exceeding existing monitor-related job budget.
- Backfill job runs idempotently.

### Open / not covered

- Whether to expose the on-demand reconcile endpoint in the public API or admin-only.
- UI surfacing of "this is inherited from System X" beyond what PR #3394 already provides.

## Phase 3 — Monitor Aggregate Statistics Refresh (fidesplus)

Driving use case 2 from `01-design.md` §3.2. Replaces the "Phase 3" entry in the existing aggregate statistics implementation plan with a concrete, framework-driven design.

### Scope

- Define event type(s) in `fidesplus.api.events.monitor_events`:
  - Recommended: `MonitorOperationCompleted(monitor_config_key: str, operation_type: str)` as a single event class.
  - Operation types: `promote`, `confirm`, `classify`, `review`, `mute`, `unmute`, `monitor_execution`. (Granularity TBD — see open question §10.3 of design doc.)
- Add `publish_after_commit` calls (and optionally `@publishes(...)` markers per design doc §6.5) on the relevant repository / service methods. Apply the recommended publish-from-repository pattern (§6.6) where practical. Targeted call sites:
  - `discovery_monitor_promotion.py:promote_resources` (and the Celery task that calls it).
  - Mute / unmute controllers: `discovery_monitor_actions_controller.py` (and equivalents under `web_monitor`, `identity_provider_monitors`).
  - Classification / review action handlers (location to confirm during implementation).
  - The `monitor_execution` context manager exit (lifecycle event for completed monitor runs).
  - Bulk action variants (mute/unmute/promote in `identity_provider_monitors.py`).
- Build the stats refresh subscriber:
  - `@subscribes_to(MonitorOperationCompleted)` handler.
  - Reuses the existing recompute logic in `fidesplus/api/discovery_monitor/aggregate_statistics/`.
  - Debounces using the existing Redis lock pattern (`aggregate_stats_refresh_lock` keyed by monitor config key) — extend the existing lock helper with a per-monitor key.
  - 30s debounce window (configurable; matches the existing skip-if-fresh buffer).
- Reconciler: no new code. The existing `initiate_aggregate_stats_refresh` (APScheduler) keeps running with its current cadence. The event-driven path reduces how often it does meaningful work; it does not replace it.

### Tests

- Publish-path unit tests at each call site (assert event registered on session post-commit).
- Subscriber tests: handler invokes recompute for the affected monitor; debounce skips back-to-back invocations within window.
- Reconciler tests: existing tests still pass; add a "events stopped flowing" scenario verifying the reconciler still hits stale rows.

### Acceptance criteria

- Per-monitor stats are refreshed within (debounce_window + dispatch_latency) of any tracked operation, in steady state.
- Reconciler-driven refreshes drop in frequency proportional to the volume of event-driven refreshes.
- No regression on the existing aggregate stats endpoint behavior.

### Out of scope (deferred to follow-up tickets)

- Time-series snapshotting (Phase 3.3 of the original aggregate stats plan) — orthogonal to event-driven refresh.
- Refresh prioritization (e.g. recently viewed monitors first) — premature without observed need.

## Cross-Phase Concerns

### Configuration

- Add framework-level settings (if any beyond defaults) under existing config sections; do not introduce a new `events` config namespace unless multiple knobs emerge.
- Per-subscriber tuning (queue overrides, debounce windows) lives in the subscriber's package, not the framework.

### Deployment

- No helm or compose changes required for Phase 1, 2, or 3. The "Other" worker covers all subscribers by default.
- A future high-volume subscriber may motivate a dedicated queue + worker — handled per the operational lever in `01-design.md` §5.4.

### Migration / backfill

- Phase 1: no migration; pure code.
- Phase 2: backfill task on rollout (see above). No schema changes required by the framework itself; PR #3394 already lands the relevant `monitorsteward` columns.
- Phase 3: no migration; pure code.

### Rollback strategy

- Phase 1 has no production effect — it can be merged dark and reverted with no operational consequence.
- Phase 2: disable by toggling all `inherit_system_stewards` to `false` (effectively halts the subscriber's effect) or by removing the subscriber registration. The reconciler is similarly togglable. Existing inherited steward rows can be cleaned up by a one-off task if rollback is permanent.
- Phase 3: disable by removing the subscriber registration. Stats refresh falls back to pure interval-driven (current state). No data integrity concerns.

## Sequencing & Dependencies

```
Phase 1 (framework plumbing, fides OSS)
    │
    ├─► Phase 2 (stewardship inheritance)
    │
    └─► Phase 3 (stats refresh)
```

Phase 1 must land before either consumer phase begins. Phase 2 and Phase 3 are independent and may run in parallel.

PR #3394 (fidesplus) and its fides counterpart (#7888) are dependencies of Phase 2 specifically — Phase 2 cannot ship until those land, since they introduce the `source` / `source_system_id` / `inherit_system_stewards` schema the subscriber operates on.
