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

**When a resource is promoted, all of its assigned systems are created if they don't
already exist (create-if-absent, idempotent).**

- **Compass/inventory** → already exists; promotion just links the resource to it.
- **Suggested** → does _not_ exist as a real System until a resource assigned to it is
  promoted. Promotion materializes it, keyed by its stable `fides_key` (and `vendor_id`
  when Compass-matched). Reuse the website-monitor pattern (`create_system_from_vendor`).
- **New (user-created)** → already created at assign time; promotion just links.

Net: **assignment is staged intent; promoting a resource guarantees its systems exist,
creating any that are missing.** Re-promoting never duplicates a system.

## Multi-system membership

A resource can be assigned to **multiple systems**. This does **not** duplicate the
resource — it is one resource record that is a _member_ of several systems (a
resource↔system association, not copies).

## How promotion works across multiple systems (per-resource)

Promotion is a **per-resource** action, taken in the main resource list (a resource's
Approve button, or the list's bulk Approve). The explorer tree is navigation/filtering
only — there is **no "promote this system"** action.

Promoting a resource realizes it under **all** of its assigned systems at once, creating
any that don't yet exist.

Example — resource **X** is assigned to **A, B, C**; you promote **X**:

- A, B, C are each created in the inventory if absent (create-if-absent).
- X is linked to / monitored under **A, B, and C** together.

A system shared by multiple resources is created the first time _any_ resource assigned to
it is promoted; other resources assigned to that system stay **pending** until they are
each promoted.

**Data-model note:** resource↔system associations still exist (one resource can be a
member of several systems); promotion promotes **all of a resource's memberships at
once**, with system create-if-absent keyed by `fides_key` / `vendor_id`.

## Current state & gaps (what to build)

- **Cloud-infra promotion is unimplemented** — `cloud_infra_monitor/base.py`
  `promote_staged_resource()` raises `NotImplementedError`.
- **Model is single-system today** — `StagedResource.system_id` /
  `user_assigned_system_id`. Multi-system membership + per-membership promotion needs a
  model change (a resource↔system association carrying its own promotion/diff status).
- **Create-if-absent on promotion already exists** for website monitors
  (`create_system_from_vendor`) — reuse for compass-matched and suggested systems.
- **The frontend mock** promotes per resource (row / bulk Approve in the list) and only
  flips `diff_status` — it does **not** actually create systems (there is no inventory in
  the mock). Treat it as UX exploration; create-if-absent + linking is the backend's job.

## UX/UI suggestions (optional)

- Tags on a resource distinguish **suggested** (sparkle) from systems that already exist
  in inventory/Compass or are user-created (generic system icon), so it's clear which are
  staged vs. real.
- Keep distinguishing suggested (sparkle) vs. inventory (logo) vs. new (generic) in the
  assign dropdown and tree so users see which systems will be created on promotion.
- Optional: when promoting a resource that will create new systems, a light "promoting
  will add N new systems to your inventory" hint on the confirm/toast.
