# Cypress E2E Tests

This folder is meant to contain true end to end tests for Fides applications. Unlike Cypress tests nested within `admin-ui` or `privacy-center`, these tests do not stub any of their endpoints, and instead they require running against the Fides test environment set up.

## Running

First, start up the test environment. This will spin up all relevant servers and frontend services. From the root directory of this repo:

```
nox -s fides_env(test)
```

Admin UI will be found at `localhost:3000` and Privacy Center at `localhost:3001`.

Then, in this folder:

```
npm run cy:run
```

### Environment variables

We specify environment variables for our server URLs so that it is possible to run the test suite against different environments. These can be found in [cypress.config.ts](./cypress.config.ts) and each one can be overwritten by prefixing with `CYPRESS_`. For example:

```sh
export CYPRESS_ADMIN_UI_URL="http://localhost:8080"
```

## Development notes

Because we are testing full end to end, changes Cypress makes will propagate to the test database and be saved. This means the tests we write here are ideally resilient to data in the database. Therefore, for example, we may not be able to say "Approve the privacy request", but instead may have to say "Approve the most recent privacy request" since another test may have added a privacy request, or we ourselves may have added another privacy request while developing the test.

Also, because we are testing multiple applications that interact with one another, we may have to cross origins. Cypress 12 introduced this feature, though there are still some experimental features within it. Before using `cy.origin`, make sure to read [the documentation](https://docs.cypress.io/api/commands/origin) as there are some interesting caveats with it.
