# Deployment

The easiest way to deploy Fides is with `Docker`. There are separate containers for `Fidesctl`, the `Server` and the `DB`.

## Application Variables

These are the environment variables that can be set to configure the CLI for a specific deployment:

* `FIDES_SERVER_URL` - The URL of the Fides webserver

After deploying the `Server` and `DB`, you need to inject the `FIDES_SERVER_URL` that points to wherever the `Server` got deployed.
