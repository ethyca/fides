# Event Framework — Technical Design

A lightweight in-application event framework for **asynchronous reactive work** — emitting an event when something happens, and dispatching registered handlers to react asynchronously, without coupling the publisher to its consumers.

## 1. TL;DR

- **Transport**: Celery, with the existing Redis broker. No new infrastructure.
- **Programming model**: typed event entities (frozen dataclasses) + decorator-registered subscribers + autodiscovery.
- **Operational home (default)**: `fides` Celery queue, picked up by the existing "Other" worker. Subscribers can opt into a dedicated queue / worker if a deployment justifies it.
- **Delivery semantics**: at-least-once, **not guaranteed**. Subscribers must be idempotent against current state. Where the work has correctness implications, an independent reconciler is required.
- **Where the bones live**: fides OSS. fidesplus (and other consumers) register subscribers and emit events.

The framework is purposefully narrow on what it promises. See §2 for the prescriptive when-to-use boundary, which exists to prevent accidental misuse.

Although informally referred to as "pub/sub", the framework does not implement on-the-wire pub/sub semantics (Redis Pub/Sub, Streams, etc.). Fan-out is handled via the in-process subscriber registry; the wire transport is point-to-point Celery dispatch per (event, subscriber) pair. See §5.3 for why.

For implementation phasing and rollout, see `02-implementation-plan.md`.

## 2. When to Use vs. When NOT to Use

This is the most important section in the doc. Default to *not* using the framework if a use case does not clearly map onto the left column.

| ✅ Use the framework when... | ❌ Do NOT use when... |
|---|---|
| The work is **asynchronous reactive work**: something happens, work happens later in response. | **Request-critical or synchronous** — the publisher needs the result before responding. |
| **Eventual consistency is acceptable** (subscriber lag of seconds-to-minutes is fine). | **Exactly-once delivery, strict ordering, or audit-grade** event-sourcing requirements. |
| Subscribers are **idempotent** — running the same handler twice produces the same end state. | **High-frequency per-row signals** — e.g. one event per staged-resource update. Use bulk/debounced events instead. |
| Where correctness depends on the work happening, a **reconciler** can produce the correct end state independently of event delivery. | The work needs **guaranteed delivery** with no reconciliation path. |
| The publish point is in a **session-aware context** (so transactional safety holds). | The publish point is **detached from a session** — e.g. a background worker not associated with a transaction. |

### 2.1 Non-Goals

The following are explicit non-goals. Surface them when reviewing new use cases. They are listed in order of how strongly they should be stressed.

- **The framework does not guarantee delivery.** Process crashes between commit and dispatch, broker unavailability, or worker errors can drop events. If your use case cannot tolerate event loss, this framework is not the right choice.
- **The framework does not provide ordering guarantees.** Events can be observed out of order across publishers and across subscribers. Subscribers must not rely on order.
- **The framework is not a replacement for synchronous calls.** If a route's response correctness depends on the work happening, do the work synchronously in the request.
- **The framework does not detect missed publishes.** If a publisher forgets to emit, the framework cannot tell. The mitigation is convention (publish from a session-aware chokepoint, see §6.6 for the recommended pattern) and the per-subscriber reconciler. New mutation paths that bypass the convention will silently miss events; this is acceptable only because every correctness-sensitive subscriber recovers via reconciliation.
- **The framework is not a generic message bus.** It is an in-application event dispatcher scoped to fides + fidesplus. It does not bridge to external systems (Kafka, SNS, webhooks, etc.).
- **The framework is not pub/sub on the wire.** Despite the colloquial name, fan-out happens through the in-process subscriber registry, not Redis Pub/Sub or Streams.

## 3. Motivation & Driving Use Cases

Several upcoming features require asynchronous reactive work in response to application state changes. Each could be implemented as a one-off Celery task plus a remember-to-call-it discipline. Doing so for every such feature produces:

- Coupling between the publisher (the action) and every consumer (the reaction), making it hard to add new consumers without modifying every action site.
- An ever-growing list of "remember to call X when you do Y" rules with no architectural enforcement.
- Inconsistent observability, retry, and reconciliation patterns across features.

A small framework that standardizes the *shape* of this work — typed events, registered subscribers, explicit publish points, recommended reconciler pattern — pays off across the next several features even though the first two consumers don't strictly require it.

The two driving use cases below establish the constraints. The framework is shaped to fit them well; future use cases that don't fit this shape should be questioned (per §2).

### 3.1 Use Case 1: Monitor Stewardship Inheritance

Per `system-integration-link/02-technical-design.md` §5 (Steward Inference Design) and [fidesplus PR #3394](https://github.com/ethyca/fidesplus/pull/3394), monitors can inherit data stewards from their linked systems.

**Data model** (post-PR-3394):

- `System.data_stewards` — many-to-many to `FidesUser` via `systemmanager`.
- `monitorconfig.inherit_system_stewards: bool` (default true on new monitors; false on backfilled).
- `monitorsteward.source` ∈ {`explicit`, `inherited`}.
- `monitorsteward.source_system_id` — populated when `source = inherited`.
- `system_connection_config_link` joins systems to connection configs; `monitorconfig.connection_config_id` links monitors to connection configs.

**Propagation graph**:

```
System.data_stewards
  → SystemConnectionConfigLink (system_id = $system_id)
    → ConnectionConfig
      → MonitorConfig (where inherit_system_stewards = TRUE)
        → MonitorSteward rows (source = "inherited", source_system_id = $system_id)
```

**Triggers**:
- `System.data_stewards` membership changes.
- `system_connection_config_link` rows added / removed.
- `monitorconfig.inherit_system_stewards` toggled on / off.
- `MonitorConfig.connection_config_id` reassigned (rare).
- New `MonitorConfig` created with `inherit_system_stewards = TRUE`.

**Subscriber's job**: for each affected monitor, reconcile its inherited `monitorsteward` rows with the union of `data_stewards` across linked systems. Add missing inherited rows, delete now-stale inherited rows, leave explicit rows untouched.

**Reconciler**: a periodic full-sweep task that re-derives inherited stewardship for every monitor with `inherit_system_stewards = TRUE`, regardless of whether events fired. Runs on an APScheduler cadence and on demand via a manual API endpoint. Cadence is product-driven and should be tight enough that *functional* staleness (see below) is bounded.

**Subscriber lives in fidesplus** (under the discovery monitor service area). Events are emitted from fides OSS where `System.data_stewards` and the link table live; fidesplus may emit additional monitor-side events (e.g. `MonitorInheritanceFlagChanged`).

**Why this fits the framework**:

- **Eventual consistency is acceptable** — but with a tighter latency tolerance than display-only freshness. Until propagation runs, inherited stewardship is genuinely not in effect (a user expecting access via inheritance does not have it). Reconciler cadence should reflect this; "minutes" is acceptable, "hours" is not.
- The work is **bounded and idempotent** against current state. Reconciling inherited rows for a monitor twice in a row produces the same result.
- The publisher (the System mutation site) does not need the propagation result.
- A **reconciler is straightforward** — full sweep over inheriting monitors. Bounded by the number of monitors with the flag set.

### 3.2 Use Case 2: Monitor Aggregate Statistics Refresh

Per the in-flight monitor aggregate statistics work (ENG-2780 / ENG-2923, Phase 3 of the implementation plan), the per-monitor statistics cache (`monitor_aggregate_statistics`) should be refreshed when operations affect a monitor's data, rather than purely on an interval.

**Triggers**:
- `promote` / `confirm` of staged resources.
- `classify` / `review` actions.
- `mute` / `unmute` of staged resources.
- A monitor execution (detection / classification / promotion task) completing.
- *Implicit*: any future state-changing operation on staged resources or a monitor.

**Subscriber's job**: for the affected `monitor_config_key`, recompute statistics and upsert into `monitor_aggregate_statistics`. Should debounce — a single recompute within a short window (e.g. 30s) of the most recent event suffices for a burst of operations on the same monitor.

**Reconciler**: already in place. `initiate_aggregate_stats_refresh` (APScheduler) periodically refreshes any rows older than the staleness skip buffer. The event-driven path reduces how often the reconciler does meaningful work; it does not replace it.

**Subscriber lives in fidesplus** (alongside the existing aggregate statistics package). Events are emitted from fidesplus (the actions all live there).

**Why this fits the framework**:

- **Eventual consistency is acceptable** — UI showing slightly stale aggregate stats is fine. There is no functional impact, only display freshness.
- The work is **bounded and idempotent** against current state — recomputing a monitor's stats twice gives the same result.
- The publisher (the operation's call site) does not need the recompute result.
- A **reconciler already exists** — the framework just reduces how often it does meaningful work.
- The "implicit" trigger above is the staleness risk: as new ways to operate on a monitor are added, each new call site must remember to publish. The framework makes the subscription-side architectural (one handler, one event type) but cannot itself prevent missed publishes — that's on the publish convention (§6.6) plus the reconciler.

## 4. Design Principles

1. **Explicit publishing.** No implicit ORM or model event listeners. Publishers call `publish_after_commit(...)` directly. Visibility wins over magic.
2. **Typed events as domain entities.** Frozen dataclasses, not Pydantic schemas. Events are internal data representation, not API surface. (Pydantic is reserved for API I/O per the established backend convention.)
3. **Idempotent + reconcilable subscribers.** Subscribers re-read current state and converge; they do not depend on payloads being authoritative. Where correctness matters, an independent reconciler is the floor.
4. **Operational continuity by default.** Subscribers ride existing Celery workers (the "Other" worker) by default. Dedicated workers are an opt-in tuning lever per subscriber, not a framework requirement and not a framework prohibition.
5. **Boring transport.** Celery + existing Redis broker. No new infrastructure dependencies.

## 5. Architecture

### 5.1 Components

```
┌────────────────────────────┐
│ Caller (repository,        │
│ service, or other          │   publish_after_commit(session, event)
│ session-aware context)     │   ──────────────────────────────►
│   ...                      │
│   publish_after_commit(...)│
└────────────────────────────┘
              │
              ▼ (after session commits)
┌────────────────────────────┐
│ Dispatcher                 │   for handler in registry[type(event)]:
│  - looks up registry       │     celery.send_task(handler.task, payload)
│  - serializes payload      │
│  - dispatches to Celery    │
└────────────────────────────┘
              │
              ▼
┌────────────────────────────┐
│ Celery (existing Redis     │   one task per (event, subscriber)
│ broker, "Other" worker     │   — or dedicated worker per opt-in queue
│ by default)                │
└────────────────────────────┘
              │
              ▼
┌────────────────────────────┐
│ @subscribes_to handler     │   deserialize payload → handler(event)
│  - reads current state     │   subscriber-specific logic
│  - writes derived state    │
└────────────────────────────┘

         (independent of event flow)
┌────────────────────────────┐
│ Reconciler (APScheduler)   │   periodic task that converges to the
│  - reads source state      │   correct end state regardless of event
│  - reconciles derived state│   delivery (required where correctness
│                            │   depends on the subscriber)
└────────────────────────────┘
```

### 5.2 Transport Choice: Celery + Redis (existing)

Celery is the existing async work executor in both repos. Using it for event dispatch:

- **Reuses retries, signals, observability, and the "Other" worker.** The transport is operationally invisible — subscribers look like Celery tasks because they are Celery tasks.
- **Decouples publishers from subscribers via the registry**, not via the broker. Multiple subscribers per event are supported; the dispatcher fans out by enqueueing one task per registered handler.
- **No new infrastructure.** Same Redis instance, same broker config, same worker tier.

A future use case requiring different delivery characteristics (stronger guarantees, true wire-level fan-out) can introduce a *second* transport behind the same `publish_after_commit` API. The programming model does not need to change to accommodate that.

### 5.3 Alternatives Considered

#### 5.3.1 Redis Streams (rejected)

Native at-least-once via consumer groups + on-the-wire fan-out. Rejected because:

- Reinvents retry / DLQ / observability that Celery already provides.
- Cluster-mode (`config.redis.cluster_enabled`) constrains stream keys to a single hash slot — keyspace discipline forever after.
- No async Redis client in-tree; introducing one adds maintenance.
- Requires long-lived consumer processes — a net-new operational tier.
- Both day-one use cases have a single subscriber. Fan-out is satisfied by the registry without on-the-wire fan-out.

#### 5.3.2 Redis Pub/Sub (rejected)

Lightest weight on the wire; true fan-out semantics; at-most-once is acceptable for the day-one use cases. Rejected nevertheless because the wire-level lightness does not survive contact with a production deployment:

- **Where do subscribers run?** Webserver pods are out (every pod receives every message → N-handlers-per-event unless we build per-event distributed locks or partitioning, *plus* heavy SQL recomputes would compete for request threads). Celery workers don't natively hold long-lived `SUBSCRIBE` connections, and pinning a handful of workers to do so fights the worker model. The realistic option is a dedicated singleton subscriber pod — i.e. a *new* pod tier, just to hold the wire connection.
- **The handler work still wants to run in Celery.** DB connections, retries on transient errors, structured task observability — all of which Celery gives us. So a Pub/Sub deployment becomes Pub/Sub-on-the-wire → bridge process → Celery task dispatch → handler. That bridge process is operational overhead Celery's own dispatch does not have.
- **No backpressure**: slow subscribers get disconnected by Redis when client output buffers exceed `client-output-buffer-limit pubsub`. This needs detection and reconnect logic.
- **No DLQ, no metrics, no built-in retries** — would be reinvented per subscriber.

Net: the protocol-level lightness pays itself back at the deployment level. For wire-level fan-out to many connected processes (cache invalidation across web pods, live SSE push to admin-UI sessions, etc.) Pub/Sub is genuinely the right tool — see §5.5 for how that future is preserved.

#### 5.3.3 Postgres LISTEN/NOTIFY + transactional outbox (rejected)

Strongest delivery guarantee — events written in the same transaction as the data, published via NOTIFY or polled from the outbox. Rejected because:

- Both day-one use cases tolerate event loss with reconciliation; the complexity buys correctness we don't need.
- Adds a new long-lived listener tier (LISTEN holds a session connection; pgbouncer-incompatible).
- Additional schema (outbox table) and migration for every consumer.
- Can be revisited as a second transport if a future use case requires it; no change to the publish API.

#### 5.3.4 SQLAlchemy `event.listen` hooks (rejected)

Considered as the publish trigger to avoid the "remember to call publish" problem. Rejected because:

- Bypassed by core-level writes (`Session.execute(update(...))`, `bulk_insert_mappings`, raw SQL) — silent missed events.
- Invisible at the call site — the debug story becomes "the hook fires somewhere, look at all model files."
- Doesn't catch all the triggers we care about (e.g. composite mutations across multiple tables).

### 5.4 Deployment Topology

- Subscribers default to the `fides` Celery queue.
- The existing **"Other" worker** (configured with `--exclude-queues=...` per `fides-helm/fides/templates/fides/worker-deployment.yaml`) automatically picks them up. This matches the public docs guidance: *"Always configure an 'Other' worker to handle messaging tasks and new task types released by Ethyca"* (`fidesdocs/pages/platform/workers.mdx`).
- A subscriber can opt into a dedicated queue by overriding `@subscribes_to(queue="...")`. The deployment can then add a worker pinned to that queue — same lever already used for the optional `worker-messaging` deployment. **This is a per-subscriber, per-deployment tuning decision; the framework neither requires nor prohibits new pod types.**

### 5.5 Future Transports

The `publish_after_commit` API is transport-agnostic. The dispatcher reads from the registry and routes events to handlers; the wire mechanism is an implementation detail.

If a future use case needs wire-level fan-out — e.g. cache invalidation across web pods, live SSE/websocket push to connected admin-UI sessions, in-memory state synchronization — the framework can grow a Redis Pub/Sub transport (or another) behind the same publish API. Subscribers for those events would declare a different transport via the decorator; existing Celery-backed subscribers are unaffected.

This preserves the option without paying for it now.

## 6. Programming Model

### 6.1 Event Types — Frozen Dataclasses

Events are **domain entities** — frozen dataclasses, not Pydantic schemas. Pydantic is reserved for API surface; events are internal data representation per the established backend convention (cf. `entities.py` per the system-integration-link package).

```python
# fides/api/events/system_events.py (or per-domain modules)

from dataclasses import dataclass

@dataclass(frozen=True)
class SystemDataStewardsChanged:
    """Emitted when the data stewards on a System change.

    Subscribers must read current state for the steward list — by the
    time a subscriber runs, the membership may have changed again.
    """
    system_id: str
```

Conventions:
- `frozen=True` (events are immutable values).
- One dataclass per event type. Past-tense names: `SystemDataStewardsChanged`, `MonitorOperationCompleted`, `SystemConnectionLinkChanged`.
- Payload contains **identifiers only**, not state. Subscribers read state at execution time.
- Located in `events/` packages alongside the domain that emits them.
- A dataclass field that is itself complex should be a JSON-serializable primitive or another frozen dataclass — events are serialized to Celery payloads and deserialized in worker processes.

There is no central `EventType` enum. The dataclass type itself is the event identity.

### 6.2 Publishing — `publish_after_commit`

```python
from fides.api.events import publish_after_commit
from fides.api.events.system_events import SystemDataStewardsChanged

class SystemRepository:
    def set_data_stewards(self, system_id: str, user_ids: list[str]) -> None:
        # ... write the change ...
        publish_after_commit(
            self.session,
            SystemDataStewardsChanged(system_id=system_id),
        )
```

Behavior:
- Registers an `after_commit` callback on the SQLAlchemy session.
- If the transaction commits → events publish in registration order (one Celery dispatch per (event, subscriber) pair).
- If the transaction rolls back → callbacks never fire; no phantom events.
- If the process dies between commit and dispatch → events are dropped; reconciliation recovers (where applicable).
- Multiple `publish_after_commit` calls within one transaction → batched in registration order.

The publisher must call this from a session-aware context. **Detached / sessionless publishing is intentionally not supported.** A sessionless publisher would lose the transactional guarantee (no rollback semantics), which is the whole point of `after_commit`.

### 6.3 Subscribing — `@subscribes_to`

```python
from fides.api.events import subscribes_to
from fides.api.events.system_events import SystemDataStewardsChanged

@subscribes_to(SystemDataStewardsChanged)  # default queue: "fides"
def propagate_inherited_stewardship(event: SystemDataStewardsChanged) -> None:
    monitors = MonitorConfigRepository(...).list_inheriting_monitors_for_system(event.system_id)
    for monitor in monitors:
        reconcile_inherited_stewards(monitor, event.system_id)
```

Behavior:
- Each `@subscribes_to(...)` registers an in-process handler and creates a Celery task that the dispatcher will call.
- The handler receives a *deserialized event instance* (the dataclass).
- A `queue=` argument overrides the default queue: `@subscribes_to(EventType, queue="fidesplus.high_volume_propagation")`.
- Multiple subscribers per event are supported. Each runs as an independent Celery task with independent retries.
- A subscriber for an event type defined in a different repo is supported (fidesplus subscribes to fides events) as long as the event class is importable.

Subscriber autodiscovery follows the existing `autodiscover_task_locations` pattern (`fides/api/tasks/__init__.py`, extended in `fidesplus/api/worker/__init__.py`). Each app registers its subscriber package paths at import time.

**Subscriber module hygiene.** Subscriber modules are imported on **both** webserver and worker:

- On the webserver, so that the dispatcher's in-process registry is populated and `publish_after_commit` knows where to dispatch.
- On the worker, so that the Celery task wrapper is registered and can execute the handler.

This means import-time side effects in subscriber modules — heavy imports, network calls or DB lookups at module top level, expensive initialization — leak into the webserver boot path. Keep module-level imports minimal and side-effect-free; defer any expensive setup to inside the handler function (or to a fixture / lazy initializer). Same rule that already applies to Celery task modules.

A subscriber whose module is not imported in a given process is invisible to the registry in that process, and `publish_after_commit` will treat its event type as having no subscribers there. This is correct behavior for the cross-repo case (a fides-OSS-only deployment without fidesplus loaded simply has no fidesplus subscribers registered) but is also the import-time coupling that makes "minimal module-top-level work" a hard rule, not a polite suggestion. If this coupling ever becomes load-bearing, manifest-based registration — declaring `(event_type, task_name, queue)` in a static manifest read at boot, without importing the subscriber's code — would be the path to relax it. Out of scope for v1.

### 6.4 Reconciliation — Required for Correctness-Sensitive Subscribers

Where the subscriber's work has **correctness implications** — that is, where the system is in a *wrong* (not just stale) state until the work runs — an independent reconciler is required.

The framework's correctness contract for these subscribers:

> *If event flow stops entirely, the system reaches the correct end state on the reconciler's cadence.*

Implications for reviewers:
- A new correctness-sensitive subscriber PR includes its reconciler (typically an APScheduler job) and tests for the reconciler.
- Design review focuses on the reconciler — its scope, frequency, blast radius — at least as much as on the event-driven happy path.
- A subscriber whose reconciler would be prohibitively expensive (full O(N) sweep over a large table on a tight cadence) is a sign the work is the wrong shape for this framework. Question the use case before optimizing the reconciler.

A subscriber whose work is purely cosmetic / freshness-only (e.g. UI display) does not strictly require a reconciler — but the design review should be explicit about that classification.

### 6.5 `@publishes` Marker (Optional Convention)

The `@publishes(EventType, ...)` decorator is an **optional convention**, not a framework requirement. It exists to improve the visibility and reviewability of the publish discipline described in §6.6.

```python
@publishes(SystemDataStewardsChanged)
def set_data_stewards(...) -> None:
    ...
    publish_after_commit(self.session, SystemDataStewardsChanged(...))
```

Three uses:

1. **Documentation.** Reviewers immediately see what events the method emits. Greppable and meaningful in PR diffs.
2. **Static registry.** A test can collect every `@publishes` marker and assert every declared event type has at least one publisher in tree, and every subscriber's event type has at least one publisher.
3. **Test-time check.** A test helper introspects `@publishes`-marked methods and asserts each one calls `publish_after_commit` for its declared event type.

The marker is not load-bearing at runtime. A method that calls `publish_after_commit` without the marker still publishes correctly. The marker is a hygiene tool, not a gate.

### 6.6 Recommended Pattern: Publish from a Repository Layer

This is a **recommended best practice**, not a framework requirement.

The framework requires only that `publish_after_commit` be called from a session-aware context. Publishing can technically happen from a repository, a service, or even a route handler.

We *recommend* publishing from a repository (or service) layer because:

- It puts the publish call adjacent to the mutation that triggers it — visible in the same diff during review.
- It centralizes the "remember to publish" decision: if a new caller of `set_data_stewards` is added, the repository method already publishes; the new caller doesn't need to remember.
- It aligns with the broader Routes → Services → Repositories direction.

A subscriber whose correctness depends on every relevant mutation publishing should pair this convention with a reconciler — the convention reduces drift but does not eliminate it.

For the day-one use cases (§3), we plan to migrate the relevant mutation paths to a repository layer as part of feature implementation. See `02-implementation-plan.md`.

## 7. Failure Modes & Mitigations

| Failure mode | Mitigation |
|---|---|
| Phantom event from rolled-back transaction | `publish_after_commit` registers on `after_commit`; never fires on rollback. |
| Process crash between commit and dispatch | Event dropped. Reconciler corrects (if subscriber has one). |
| Broker unavailable | `send_task` raises; dispatcher logs and continues to the next event. Reconciler corrects. |
| Subscriber raises | Standard Celery retry policy applies. After max retries the task fails into the result backend. Reconciler corrects. |
| Slow subscriber backs up the queue | Operational lever: split the slow subscriber off to its own queue + dedicated worker. |
| Stale payload (state changed between commit and subscriber run) | Subscribers read current state. Thin payloads remove reliance on payload contents. |
| Duplicate dispatch (Celery `acks_late` redelivery) | Subscribers are idempotent against current state; running twice produces the same end state. |
| Missed publish (publisher forgot to emit) | Reconciler corrects (for correctness-sensitive subscribers). For freshness-only subscribers, the next legitimate publish closes the gap. |

The throughline: every failure mode either has no observable effect (reconcile and converge) or surfaces in standard Celery operational signals (failed tasks, queue depth, worker logs).

## 8. Observability

Three structured-logging points:

- **Publish**: `event_type`, `event_id` (UUID generated at publish time), `publisher` (file:function via `inspect`), `session_id`.
- **Dispatch** (per-subscriber, after commit): `event_id`, `event_type`, `subscriber_name`, `task_id` (Celery), `queue`.
- **Handle** (in subscriber task): start, end, latency, outcome. Errors include stack trace.

The Celery `request_id` propagation pattern in `fides/api/tasks/__init__.py` (via `before_task_publish` / `task_prerun` / `task_postrun` signals) is the model — the same mechanism extends to `event_id` propagation through the worker context.

`event_id` is generated once at `publish_after_commit` time. All subscribers for that publish carry the same `event_id`. This makes it possible to trace a single logical event across multiple subscriber tasks in logs.

Metrics are out of scope for v1 but the logging is structured so operators can derive volume / latency / error rate via log queries.

## 9. Adding a New Event or Subscriber — Checklist

When adding a new event:

1. Define the dataclass in the appropriate `events/` package. Frozen, identifier-only payload, past-tense name.
2. Identify the publish point. It MUST be called from a session-aware context. We recommend a repository or service method (see §6.6).
3. Optionally add `@publishes(EventType)` on that method (see §6.5).
4. Call `publish_after_commit(session, EventType(...))` after the mutation but before return.
5. Add or extend an integration test that exercises the publish path and asserts the event is registered on the session.

When adding a new subscriber:

1. Define the handler function decorated with `@subscribes_to(EventType, queue=...)`. Default the queue unless deployment characteristics justify a dedicated one.
2. The handler reads current state. Use payload only for identifiers.
3. Decide whether the subscriber is correctness-sensitive (§6.4). If yes, define (or extend) a reconciler that produces the correct end state independently of event delivery, and wire it into APScheduler.
4. Add subscriber tests (happy-path) and, for correctness-sensitive subscribers, reconciler tests (the case where events stopped flowing).
5. Update operational docs if the subscriber requires a non-default queue.

## 10. Open Questions

1. **Marker enforcement strictness.** Should `@publishes` be required (CI-enforced) for any method that calls `publish_after_commit`, or recommended? Leaning *recommended* for v1, hardening to *required* after a stabilization period.
2. **Reconciler cadence for stewardship inheritance.** Product-driven decision. Functional staleness (not just display staleness) gates this — until propagation runs, inherited stewardship is not in effect. Starting suggestion: every 15-30 minutes, plus on-demand API. Confirm with product.
3. **Stats event granularity.** A single `MonitorOperationCompleted(monitor_config_key, operation_type)` vs. one event class per operation. The former is simpler and the subscriber doesn't care which operation fired; the latter is more expressive for hypothetical other subscribers. Lean toward the simpler model unless a concrete second subscriber needs the distinction.
4. **Event package layout.** Proposal: `fides.api.events.<domain>` for events emitted from fides; `fidesplus.api.events.<domain>` for fidesplus-emitted events. Both repos can subscribe to events from either. Confirm before Phase 1 (see implementation plan).
5. **`event_id` provenance.** Confirmed: generated at `publish_after_commit` time, shared across all subscribers for that publish. Documented here for clarity; flag if a different model is preferred.
