# Admin UI

Admin UI for managing FidesOps privacy requests. A web application built in Next.js with the FidesUI component library.

## Running Locally

1. Run `nox -s create_user` and follow prompts to create a user. Note that password requires 8 or more characters, upper and lowercase chars, a number, and a symbol.
2. In a new shell, `cd` into `clients/ops/admin-ui`, then run `npm run dev`.
3. Nav to `http://localhost:3000/` and logged in using created user. The `email` field is simply the `user` that was created, not a valid email address.

## Testing Entire Request Flow

1. Run the `fidesops` server with `nox -s dev`.
2. Create a policy key through the API (using the fidesops Postman collection).
3. Configure the `clients/privacy-center` application to use that policy by adding it to the appropriate request config in `config/config.json`.
4. Run the Privacy Request center using `npm run dev`.
5. Submit a privacy request through the Privacy Request center.
6. View that request in the Admin UI and either approve or deny it.

## Unit test locations

Unless otherwise specified below, all unit tests should be colocated in the directory with the file(s) they are testing, in a `__tests__` subfolder.

The sole exception to this is the `pages` directory. Tests for Next.js pages live in the root `__tests__/pages` directory. Otherwise, Next.js attempts to include them in final build output, which breaks the build.
