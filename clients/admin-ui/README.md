# Admin UI

Admin UI for managing Fides privacy requests. A web application built in Next.js with the FidesUI component library.

## Running Locally

1. In a new shell, `cd` into `clients/admin-ui`, then run `npm run dev`.
1. Nav to `http://localhost:3000/` and log in using the created user. The `email` field is simply the `user` that was created, not a valid email address.

## Unit test locations

Unless otherwise specified below, all unit tests should be colocated in the directory with the file(s) they are testing, in a `__tests__` subfolder.

The sole exception to this is the `pages` directory. Tests for Next.js pages live in the root `__tests__/pages` directory. Otherwise, Next.js attempts to include them in final build output, which breaks the build.

## Feature flags

During the software development process, one or more features may not be visible at runtime. Feature flags are defined
within [flags.json](./src/flags.json).

You can toggle flags at runtime by opening the features panel, which can be accessed under the user menu in the top-right
of the page header. These changes will be saved per-browser, per-environment, until you log out or reset them from the menu.

### Environments

Feature flags can be configured independently for the development, test, and production environments:

- **development** - Running `npm run dev` uses the development environment. This will include bleeding-edge features.
- **test** - Cypress runs in the tet environment via `npm run cy:start`. This will usually match production, but
  new features may be enabled in test to verify them in CI before release.
- **production** - Only features ready for release will be enabled for production. `npm run build` always produces a
  build configured for production, which is then bundled into the Fides server.

You can switch between these environments manually by overriding the `NEXT_PUBLIC_APP_ENV` environment variable when
running the app, for example:

`NEXT_PUBLIC_APP_ENV=production npm run dev`

Or you can configure the environment using `env.local` as described by the [Next.js docs](https://nextjs.org/docs/basic-features/environment-variables#loading-environment-variables).

## Preparing for production

To view a production version of this site, including the backend:

1. Run `npm prod-export`. This will
   1. Export the static site to `out/`
   1. Copy the build from `out/` to the folder in the backend which will serve static assets at `/`
1. Run `nox -s api` in the top-level `fides` directory.
1. Navigate to `http://localhost:8000`
