# Deployment

The easiest way to deploy Fides is with `Docker`. There are separate containers for `Fidesctl`, the `Server` and the `DB`.

## Application Variables

These are the environment variables that can be set to configure Fidesctl for a specific deployment:

* `FIDES_API_URL` - The URL of the Fides webserver

After deploying the API and DB, you need to inject the `FIDES_SERVER_URL` that points to wherever the API got deployed. Fidesctl will check for this environment variable first when running any commands instead of requiring the `-u` flag.
