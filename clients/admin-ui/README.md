# Admin UI

Admin UI for managing Fides privacy requests. A web application built in Next.js with the FidesUI component library.

## Running Locally

1. In a new shell, `cd` into `clients/admin-ui`, then run `npm run dev`.
1. Nav to `http://localhost:3000/` and log in using the created user. The `email` field is simply the `user` that was created, not a valid email address.

## Testing Entire Request Flow

1. Run the fides server with `nox -s dev`.
2. Create a policy key through the API (using the Postman collection).
3. Configure the `clients/privacy-center` application to use that policy by adding it to the appropriate request config in `config/config.json`.
4. Run the Privacy Request center using `npm run dev`.
5. Submit a privacy request through the Privacy Request center.
6. View that request in the Admin UI and either approve or deny it.

## Unit test locations

Unless otherwise specified below, all unit tests should be colocated in the directory with the file(s) they are testing, in a `__tests__` subfolder.

The sole exception to this is the `pages` directory. Tests for Next.js pages live in the root `__tests__/pages` directory. Otherwise, Next.js attempts to include them in final build output, which breaks the build.

## Feature flags

During the software development process, one or more features may not be visible at runtime. To toggle a given feature, find the given feature flag `name` key located in the [flags.json](/clients/admin-ui/srcgs.json) file. Update the `isActive` key value to `true/false`. If `true`, feature will be visible at runtime. Otherwise, feature will not be visible at runtime.

For techinical reference implementation, please reference [react-feature-flags](https://github.com/romaindso/react-feature-flags).

## Preparing for production

To view a production version of this site, including the backend:

1. Run `npm prod-export`. This will
   1. Export the static site to `out/`
   1. Copy the build from `out/` to the folder in the backend which will serve static assets at `/`
1. Run `nox -s api` in the top-level `fides` directory.
1. Navigate to `http://localhost:8000`
