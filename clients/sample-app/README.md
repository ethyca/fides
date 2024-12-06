# Fides Sample App

"Cookie House", a sample web application to help demonstrate some of the features of Fides!

## Configuration

This app requires zero configuration, but does support the following ENV vars to override defaults:

| ENV var                                             | Description                                                              | Default               |
| --------------------------------------------------- | ------------------------------------------------------------------------ | --------------------- |
| FIDES_SAMPLE_APP\_\_DATABASE_HOST                   | Sample database host name                                                | localhost             |
| FIDES_SAMPLE_APP\_\_DATABASE_PORT                   | Sample database port                                                     | 5432                  |
| FIDES_SAMPLE_APP\_\_DATABASE_USER                   | Sample database username                                                 | postgres              |
| FIDES_SAMPLE_APP\_\_DATABASE_PASSWORD               | Sample database password                                                 | postgres              |
| FIDES_SAMPLE_APP\_\_DATABASE_DB                     | Sample database name                                                     | postgres_example      |
| FIDES_SAMPLE_APP\_\_GOOGLE_TAG_MANAGER_CONTAINER_ID | (optional) Google Tag Manager Container ID to inject, e.g. "GTM-ABCD123" | null                  |
| FIDES_SAMPLE_APP\_\_PRIVACY_CENTER_URL              | Fides Privacy Center URL                                                 | http://localhost:3001 |

## Development

To run locally, follow these steps:

In `/clients/sample-app`:

```bash
npm install
npm run dev
```

This will automatically bring up a Docker Compose project to create a sample app database containing the Cookie House products data, so ensure you also have `docker` running locally.

Once running successfully, open http://localhost:3000 to see the Cookie House!

Note: If you are already running a database on port 5432 locally, you can override the default port by setting the `FIDES_SAMPLE_APP__DATABASE_PORT` environment variable and ALSO changing the **host** port number in the `docker-compose.yml` file. For example:

```yaml
ports:
  - "5433:5432"
```

## Pre-commit

Before committing any changes, run the following:

```bash
npm run format
npm run lint
npm run test
```

## Testing

This app (currently!) does not have any automated tests. However, it is used in the following automated E2E suites:

- `clients/cypress-e2e/cypress/e2e`
- `clients/privacy-center/cypress/e2e`

These Cypress suites will automatically run in CI to ensure any changes to this app continue to work as expected.

## Deployment

To deploy this app, typically you should use the published `ethyca/fides-sample-app` Docker image which is production-built Next.js image. See https://docs.ethyca.com for more!
