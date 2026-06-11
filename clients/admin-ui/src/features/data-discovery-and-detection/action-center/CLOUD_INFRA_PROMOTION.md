# Cloud Infrastructure Monitor — Promotion Logic (backend spec)

## Purpose

Clarify, for backend implementation, **(1)** when a System is created in the inventory
during promotion, and **(2)** how promotion behaves when a resource belongs to multiple
systems. The cloud-infra UI today is a frontend mock; this is the intended behavior to
build against. We deliberately keep most of this invisible in the UI — the user just
"approves."

## Three kinds of systems in the assign flow

| Kind                    | What it is                                                                                       | Already in inventory? | Icon           |
| ----------------------- | ------------------------------------------------------------------------------------------------ | --------------------- | -------------- |
| **Compass / inventory** | A known system that already exists in inventory (Snowflake, Salesforce, …), usually Compass/vendor-matched | Yes                   | connector logo |
| **Suggested**           | A Fides-suggested staged business application, proposed from the detected resources; not a real System yet | No (staged only)      | sparkle        |
| **New (user-created)**  | A system the user creates on the fly while assigning                                             | Created at assign time | generic        |

## When is a System created in the inventory?

**On promotion, if it doesn't already exist (create-if-absent, idempotent).**

- **Compass/inventory** → already exists; promotion just links the resource(s) to it.
- **Suggested** → does _not_ exist as a real System until the first resource assigned to
  it is promoted. Promotion materializes it, keyed by its stable `fides_key` (and
  `vendor_id` when Compass-matched). Reuse the website-monitor pattern
  (`create_system_from_vendor`).
- **New (user-created)** → already created at assign time; promotion just links.

Net: **assignment is staged intent; the System is guaranteed to exist at promote time,
created lazily if needed.** Re-promoting never duplicates a system.

## Multi-system membership

A resource can be assigned to **multiple systems**. This does **not** duplicate the
resource — it is one resource record that is a _member_ of several systems (a
resource↔system association, not copies).

## How promotion works across multiple systems (per-membership)

Promotion is scoped to the **membership** (resource × system), not the whole resource.

Example — resource **X** is assigned to **A, B, C**; you promote **System A**:

- X is realized / monitored **under System A only**.
- X's memberships in **B** and **C** stay **pending** until B and C are each promoted.
- There is still **one** X; promoting B later realizes X under B, and so on.

Why: each system can be reviewed/owned independently — promoting one system must not
silently approve a resource into systems no one has reviewed.

**Data-model implication:** promotion/diff state must be tracked **per (resource, system)
membership**, not as a single resource-level status. "Approve System A" = promote the
pending memberships of A's resources into A.

## Current state & gaps (what to build)

- **Cloud-infra promotion is unimplemented** — `cloud_infra_monitor/base.py`
  `promote_staged_resource()` raises `NotImplementedError`.
- **Model is single-system today** — `StagedResource.system_id` /
  `user_assigned_system_id`. Multi-system membership + per-membership promotion needs a
  model change (a resource↔system association carrying its own promotion/diff status).
- **Create-if-absent on promotion already exists** for website monitors
  (`create_system_from_vendor`) — reuse for compass-matched and suggested systems.
- **The frontend mock is a simplification** — it flips one resource-level `diff_status`
  (approving via A flips X everywhere). That is _not_ the intended per-membership
  behavior above; treat the mock as UX exploration only.

## UX/UI suggestions (optional)

- On a resource assigned to multiple systems, show **per-system promotion state** (e.g. a
  check vs. a pending dot on each system tag) so it's clear X is approved in A but pending
  in B/C.
- Keep distinguishing suggested (sparkle) vs. inventory (logo) vs. new (generic) in the
  dropdown and tree (already done) so users see which systems will be created.
- Optional: on bulk approve, a light "promoting will create N new systems" note on the
  confirm modal.
