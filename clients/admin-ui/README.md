# Admin UI

Admin UI for managing Fidesctl.

## Running Locally

1. Run `nox -s api` in top-level `fides` directory
2. In a new shell, `cd` into `clients/admin-ui`, install via `npm install`, then run `npm run dev`.
3. Navigate to `http://localhost:3000/`.

## Preparing for production

To view a production version of this site, including the backend:

1. Run `npm prod-export`. This will
   1. Export the static site to `out/`
   1. Copy the build from `out/` to the folder in the backend which will serve static assets at `/`
1. Run `nox -s api` in the top-level `fides` directory.
1. Navigate to `http://localhost:8000`
