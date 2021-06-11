# Deployment

The easiest way to deploy Fides is with `pip` for the CLI and `Docker` for the Server and DB.

## Application Variables

These are the environment variables that can be set to configure the CLI for a specific deployment:

* FIDES_SERVER_URL - The URL of the Fides webserver

## Manifests

Fides ships with default data taxonomies that include standard examples, but in practice you may need to create your own to match what your organization uses in practice. This is done in the same way as declaring other objects. The following is a list of steps to both define and validate new systems within Fides.

1. spin up the db
1. `pip install fidesctl`
1. Run the server via it's docker container (`registry.gitlab.com/ethyca/fides-core/fides-server:latest`), injecting the expected env vars for the database connection
