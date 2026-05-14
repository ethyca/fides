# GraphQL on the Frontend — Proposal

**Status:** draft for discussion
**Scope:** `clients/admin-ui` only (revisit `privacy-center` / `fides-js` later)

## Background

GraphQL on the frontend has come up in several engineering discussions over the past months, from different angles but landing on the same observation: admin-ui is increasingly built around dashboards and data-heavy pages rather than the simple single-table screens that defined earlier work. REST has served the single-table pattern well — one endpoint, one resource, one response. Dashboards are a different shape. A single view typically needs slices of data from several backend resources at once: counts from one place, related entities from another, an aggregation from a third.

In practice this currently means firing five or more GET requests per page view. Two costs follow:

1. **The frontend is harder to maintain.** Each page becomes a small orchestration problem — sequencing requests, managing many independent loading and error states, stitching data together in memory.
2. **The backend carries a lot of coordination work.** Every new dashboard or composite view tends to require a new bespoke REST endpoint to assemble the right data shape, which pulls backend engineers into frontend-shaped decisions and slows both sides down.

## Approach

Full migration of admin-ui's data layer to GraphQL, **schema-first**. The SDL is the contract between FE and BE — co-authored, committed in one place, and the source of truth that both sides' codegen runs off. FE works against mocks generated from the SDL so it can ship dashboard queries end-to-end before BE resolvers exist. RTK Query stays in place during the transition and retires once all its readers have moved over. The path there is incremental — resource by resource, opportunistically, when a feature is being touched anyway. No big-bang switch, and no requirement to migrate something just because we can.

## Today's FE stack (the constraint)

Next.js 16 (Pages Router), React 19, TS. RTK Query is the data layer — one `baseApi`, ~72 slices, ~80 cache tags, code-split via `injectEndpoints`. Precedent for a sibling API exists (`v3Api`). End-to-end typed via `@hey-api/openapi-ts`. Redux + redux-persist, Formik + yup/valibot, Ant Design via fidesui.

## Client: Apollo Client

Apollo is the proposed client. It's the industry standard for GraphQL on React, has the deepest tooling (Apollo DevTools), and ships a normalized cache as the default — which is the long-term cache benefit we're after. Its bundle is the largest of the viable options (~30 KB gz) but that's acceptable in an internal admin tool.

If anyone wants to argue for an alternative, the realistic candidates are **urql** (smaller, opt-in normalized cache, less mature tooling) and **Relay** (compiler-driven, schema-first, heavier buy-in). Apollo wins on tooling maturity and team familiarity; the others are not ruled out by anything other than that.

## Codegen and mocking

`graphql-code-generator` with The Guild's `client-preset` to emit typed documents and fragment-masked hooks for Apollo. The committed SDL is the input. A new `npm run graphql:generate` script mirrors the existing `openapi:generate` workflow.

FE mocks come from the same SDL using `@graphql-tools/mock` (or MSW + graphql, depending on whether we want network-level interception for tests too). A new dashboard query can ship end-to-end against mocks before BE resolvers exist; the mock layer flips off per-operation via env config as real resolvers land.

## Phase 1 — foundation (1 sprint, 1 engineer)

1. Stand up Apollo Client as a third sibling to `baseApi` and `v3Api` in the Provider tree.
2. Wire codegen against the committed SDL.
3. Wire auth: read token from Redux, reuse `addCommonHeaders` via an Apollo link.
4. Add the mock layer so FE can run end-to-end against mocks.
5. Ship two dashboard queries — against mocks initially, switching to real resolvers as BE lands them.
6. Document the pattern other engineers will copy.

## Phase 2+ — migration

- Close `baseApi` to net-new endpoints; new work lands on GraphQL.
- Opportunistic migration: a resource moves to GraphQL when a feature touching it requires meaningful changes. Migrate readers in the touched feature; leave other readers on RTK Query temporarily.
- Periodic cleanup waves retire RTK Query slices once all readers of a resource have moved over.
- End state: `baseApi`, `v3Api`, and the FE-facing OpenAPI codegen are removed.

## Coexistence rules during the transition

1. One source of truth per resource — never overlapping ownership between RTK Query and Apollo.
2. Cross-cache invalidation is explicit: a GraphQL mutation that affects RTK-Query-owned data dispatches `baseApi.util.invalidateTags(...)`; an RTK Query mutation that affects GraphQL-owned data triggers an Apollo refetch.
3. Shared auth plumbing — token from Redux, headers via `addCommonHeaders`.
4. Errors normalize at the boundary to `{ data, error }` so the rest of the app keeps its existing shape.
5. Forms stay agnostic — Formik consumes promises from either side.

## Top risks

- **Schema drift.** The main risk under schema-first is the SDL diverging between what FE has built against and what BE actually implements. Mitigation: a single committed SDL file, schema-diff CI checks (e.g. GraphQL Inspector), and both sides' codegen running off the same source.
- **Two cache models during transition.** Bounded by Phase 2's pace. Small ongoing overhead for cross-cache invalidation while it lasts.
- **Migration stall.** If Phase 2 stalls partway, we end up paying for both systems indefinitely. Mitigation: keep the migration rule simple (close `baseApi` to net-new) and run cleanup waves on a cadence.

## Out of scope for this document

- Backend implementation: resolver patterns, the data layer behind the schema, persisted queries. The schema *design* is jointly owned; everything behind it is BE's call.
- `privacy-center` and `fides-js` adoption.
- Subscriptions and SSR — known follow-ups, not v1.

## Decisions needed to unblock

- FE: Phase 1 owner.
- Team: agreement on the coexistence rules above (especially #1 and #2).
- Joint: where the SDL lives and how it stays in sync (likely a single file in the BE repo, FE consumes via codegen).
