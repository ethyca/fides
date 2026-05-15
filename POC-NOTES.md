# GraphQL PoC — Frontend (Apollo) notes — `graphql-poc-apollo`

Paired BE branch: `graphql-poc-be` in **fidesplus** (HEAD `e45dc01b1`; SDL unchanged since `104cba76c`).
Sibling FE branch (urql): `graphql-poc-urql` in fides.

**The real dashboard at `/` now runs on GraphQL.** There is no separate page — the existing `HomeDashboard` cards fetch through Apollo via per-card queries. The standalone `/dashboard-graphql` route and its bespoke view were removed.

## Architecture: per-card queries, drop-in hooks

Each card keeps its own query (not one combined query). Decision rationale (discussed with the team):

- **Independent auth.** Cards map to different permissions/feature flags in the real product. Per-card queries fail independently — an unauthorised card hides itself, the rest of the dashboard is unaffected — exactly mirroring the REST behaviour. One combined query would force field-level auth + partial-error handling on the client.
- **Progressive loading.** One combined query blocks the whole dashboard on the slowest resolver, and `agent_briefing` is LLM-backed (slow). Per-card preserves card-by-card spinner-then-paint.

Implementation keeps the blast radius tiny: `src/features/dashboard-graphql/hooks.ts` exports replacements with the **exact names, signatures, and return shapes** of the dashboard RTK Query hooks, mapping each camelCase GraphQL response back onto the existing snake_case `~/features/dashboard/types` interfaces. Every card changed by **one line** — its import path. Card JSX/logic is untouched.

`dashboard.slice.ts` is intentionally left in place (the priority-action update mutation stays on RTK; other code/tests may import it). The GraphQL surface replaces only the read queries the dashboard consumes.

## Try it locally

```bash
# Mocks, no BE (schema-driven via @graphql-tools/mock):
cd clients/admin-ui && npm run dev:mock-graphql

# Against the real BE (fidesplus on graphql-poc-be):
cd clients/admin-ui && npm run dev

open http://localhost:3000/        # the real dashboard, now on GraphQL
```

The dashboard cards render under the `alphaDashboard` feature flag (same as before this change).

After a schema change: `nox -s graphql_emit_schema` in fidesplus, then `npm run graphql:generate` in admin-ui.

## Comparison metrics (Apollo)

- **FE lines of code to wire the whole dashboard**
  - `queries.graphql` (8 per-card operations): ~110 lines (SDL-shaped; identical on the urql branch).
  - Provider + Apollo client + auth link: `DashboardGraphqlProvider.tsx` 13 + `apolloClient.ts` ~36 = **~49 lines**.
  - `hooks.ts` drop-in adapter layer (8 hooks + camel→snake mappers): **~250 lines**. This is the real Apollo-specific surface; most of it is the response remapping that exists only because we kept the REST-shaped card contracts.
  - Per card: **1 line** (the import path).
- **Bundle size delta**: Apollo Client + graphql ≈ **~50 KB gzipped** added. Run `npm run analyze:browser` and diff the home route chunk for an exact figure (estimate pending real measurement).
- **Setup time** (excluding shared BE): the original single-query wiring ~2 h; the per-card refactor + drop-in hook layer ~1.5 h on top.

## Rough edges

- **The adapter layer is the cost.** Keeping the existing card contracts (snake_case `types.ts`) means every GraphQL response is remapped by hand in `hooks.ts`. If the cards were rewritten to consume the generated gql types directly, that ~250-line layer mostly disappears — but then it's not a drop-in and the diff explodes across 8 components. The drop-in tradeoff is deliberate for a PoC; a real migration would bite the bullet and consume gql types directly.
- **Enum value skew.** Most enums share string values between the gql SDL and `types.ts`, *except* `TrendPeriod` (SDL `thirty_days` vs REST `30d`) — needs an explicit map. Easy to miss.
- **`ActivityFeedItem` has no `id`** in the schema, but the infinite-scroll dedupe keys on `id`. The adapter synthesises `id = ${timestamp}__${message}` so `useInfiniteActivityFeed` works unmodified. A real schema should expose a stable id.
- **`client-preset` `gql()` template-literal typing is brittle** (whitespace-sensitive). Importing the generated `*Document` constants is the reliable path; all hooks do that.
- **SDL-as-runtime-string for mocks**: no bundler-agnostic ".graphql as string" import, so `scripts/sync-graphql-sdl.mjs` writes `schema-string.ts` from `schema.graphql` during `graphql:generate`.
- **Client URL**: the endpoint is at root `/graphql`, not under `NEXT_PUBLIC_FIDESCTL_API` (`/api/v1`). The client posts to a hard `/graphql`; a Next rewrite proxies it to the backend and MSW intercepts it in mock mode. (Earlier this PoC wrongly assumed that env var was empty.)

## What ships in this branch

- `clients/admin-ui/schema.graphql` — emitted by the fidesplus PoC.
- `clients/admin-ui/codegen.ts`, `scripts/sync-graphql-sdl.mjs`, `src/__generated__/graphql/`.
- `src/features/dashboard-graphql/`: `DashboardGraphqlProvider.tsx`, `apolloClient.ts`, `queries.graphql` (8 ops), `hooks.ts` (drop-in adapters), `schema-string.ts`.
- `src/mocks/dashboard-graphql/handlers.ts` — schema-driven MSW handler (mocks every per-card query).
- 9 one-line import swaps in `src/home/*` + `_app.tsx` provider wiring + `next.config.js` `/graphql` proxy.
- npm scripts: `graphql:generate`, `dev:mock-graphql`.

## Not done / out of scope

- No mutations, no subscriptions, no SSR.
- `dashboard.slice.ts` kept (mutations + potential other consumers); only read queries moved to gql.
- No `@defer` (would mitigate the combined-query loading problem, but we went per-card instead).
- No persisted queries, Apollo Studio, or schema registry.
