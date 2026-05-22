# Fides Privacy Center

Privacy Center for Fides, A web application built in Next.js to collect privacy requests from users: access, erasure, consent, and more!

See the [UI Contribution Docs](https://ethyca.github.io/fides/dev/development/ui/overview) for guidance on running and developing the Privacy Center!

## API docs

In development builds only, the Privacy Center exposes its internal API:

- `/docs` renders a Swagger UI for the endpoints under `pages/api/*` (generated from `@swagger` JSDoc blocks).
- `/api/openapi.json` serves the raw OpenAPI schema.

Both return 404 in production builds.
