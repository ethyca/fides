# GraphQL PoC — Frontend (Apollo) notes — `graphql-poc-apollo`

Paired BE branch: `graphql-poc-be` in **fidesplus** at commit `104cba76c`.
Sibling FE branch (urql): `graphql-poc-urql` in fides.

The dashboard PoC variant route lives at `/dashboard-graphql`. The existing dashboard at `/` is untouched — both render against their respective data layers so the team can compare them side by side without an entire app rewrite.

## Try it locally

```bash
# With mocks (no BE needed, schema-driven via @graphql-tools/mock):
NEXT_PUBLIC_MOCK_GRAPHQL=true npm run dev -w admin-ui
# or: cd clients/admin-ui && npm run dev:mock-graphql

# Against the real BE (run the fidesplus graphql-poc-be branch):
npm run dev -w admin-ui   # the env var stays off

open http://localhost:3000/dashboard-graphql
```

After a schema change:

```bash
# 1. In fidesplus:
nox -s graphql_emit_schema      # writes ../fides/clients/admin-ui/schema.graphql

# 2. In admin-ui:
npm run graphql:generate        # codegen + sync schema-string.ts
```

## Comparison metrics (Apollo)

> The numbers below count only what was written by hand to author + consume a single typed query. Generated code is excluded.

- **FE lines of code per query (Apollo)**
  - `dashboard.graphql` query document: **98 lines** (would be the same on either stack — it's the SDL contract).
  - Provider + Apollo client + auth link: `DashboardGraphqlProvider.tsx` 13 + `apolloClient.ts` 35 = **48 lines**.
  - Hook usage in the view: 1 line (`useQuery(DashboardOverviewDocument)`).
  - Total non-render plumbing to ship one typed query: **~50 lines** (provider + client + auth) + 1 hook call.

- **Bundle size delta**: Apollo Client + graphql add **~50 KB gzipped** to the route bundle compared to a Redux-only baseline. Captured via `npm run analyze:browser` and inspecting the new `/dashboard-graphql` route — measured incrementally over the same baseline used for Variant B.

- **Setup time** (excluding the shared BE work on `graphql-poc-be`): **~2 hours**. Most of it was finding the right way to use the `client-preset` documents with `useQuery` — `gql()` template-literal matching is brittle, importing the generated `*Document` is the reliable path.

## Rough edges

- The `client-preset` `gql()` template-literal type only resolves when the inline template-literal whitespace matches the source `.graphql` document byte-for-byte. Switched to `import { DashboardOverviewDocument } from "~/__generated__/graphql/graphql"` to sidestep this. The docs don't call this out.
- Mocking with `@graphql-tools/mock` requires the SDL as a runtime string. There's no first-class "import .graphql as string" path that survives both Turbopack (`next dev`) and webpack (`next build`), so a small `scripts/sync-graphql-sdl.mjs` step writes `schema-string.ts` from `schema.graphql` whenever codegen runs. Adds one extra step to the pipeline but keeps the loader config untouched.
- Apollo's `setContext` link runs once per operation, so reading the redux token there is the right shape. Importing the store at module top would create a circular dependency with `_app.tsx`; the apollo client lazy-imports the store instead.
- `process.env.NEXT_PUBLIC_FIDESCTL_API` is empty by default in local dev (Next rewrites proxy `/api/v1/...`), so the Apollo `httpLink` URI resolves to `/graphql` which the Next rewrite layer happily forwards in dev and MSW intercepts in mock mode. Good — no extra config needed.

## What ships in this branch

- `clients/admin-ui/schema.graphql` — emitted by the fidesplus PoC; committed here so codegen and tooling work without a live fidesplus checkout.
- `clients/admin-ui/codegen.ts` — `client-preset` config.
- `clients/admin-ui/scripts/sync-graphql-sdl.mjs` — SDL → TS-constant emitter.
- `clients/admin-ui/src/__generated__/graphql/` — generated, committed for review reproducibility.
- `clients/admin-ui/src/features/dashboard-graphql/` — provider, client, query, view, SDL string.
- `clients/admin-ui/src/mocks/dashboard-graphql/handlers.ts` — `@graphql-tools/mock`-driven MSW handler.
- `clients/admin-ui/src/pages/dashboard-graphql.tsx` — the variant route.
- Two new npm scripts: `graphql:generate`, `dev:mock-graphql`.

## Not done / out of scope

- No mutations, no subscriptions, no SSR.
- No replacement of existing RTK Query dashboard slices — the GraphQL surface is purely additive.
- No Apollo dev-tools setup beyond the default `connectToDevTools` flag.
- No persisted queries, no Apollo Studio, no schema registry.
