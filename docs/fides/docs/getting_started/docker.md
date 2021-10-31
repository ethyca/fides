# Getting Started with Fidesctl in Docker

---

The recommended way to get Fidesctl running is via Docker-Compose. There is a `docker-compose.yml` file supplied with the repo to make running Fidesctl as easy as possible.

## System Requirements

1. Install `docker` locally (see [Docker Desktop](https://www.docker.com/products/docker-desktop) or your preferred installation; use a recent enough version so that `docker-compose` is also available). Your Docker version should be >=20.10.8, and Docker-Compose >=1.29
1. Clone the [Fidesctl repo](https://github.com/ethyca/fides) and `cd` into the top-level `fides` directory.

## Docker Setup

The following commands should all be run from the top-level `fides` directory (where the `docker-compose.yml` is):

1. `docker-compose up -d` -> Spin up a Postgres database and the Fidesctl API
1. `docker-compose run --rm  fidesctl /bin/bash` -> Open a shell within a container that has `fidesctl` pip installed and is able to communicate with the other containers. Now we can start running `fidesctl` commands directly.
1. `fidesctl init-db` ->  This runs migrations and configures the database. The output should look something like this:

    ```bash
    ~/git/fides% fidesctl init-db
    INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
    INFO  [alembic.runtime.migration] Will assume transactional DDL.
    INFO  [alembic.runtime.migration] Running upgrade  -> 26934c96ec80, initial migration
    INFO  [alembic.runtime.migration] Running upgrade 26934c96ec80 
    -> 327cd266f7b3, update dataset depth
    INFO  [alembic.runtime.migration] Running upgrade 327cd266f7b3 
    -> e576b6a80a49, add parent_key to DataQualifier
    INFO  [alembic.runtime.migration] Running upgrade e576b6a80a49 
    -> 732105cd54e3, update dataset field name
    INFO  [alembic.runtime.migration] Running upgrade 732105cd54e3 
    -> 45c7a349db68, Remove qualifier lists from data set models   
    ----------
    Processing data_use resources...
    CREATED 23 data_use resources.
    UPDATED 0 data_use resources.
    SKIPPED 0 data_use resources.
    ----------
    Processing organization resources...
    CREATED 1 organization resources.
    UPDATED 0 organization resources.
    SKIPPED 0 organization resources.
    ----------
    Processing data_qualifier resources...
    CREATED 5 data_qualifier resources.
    UPDATED 0 data_qualifier resources.
    SKIPPED 0 data_qualifier resources.
    ----------
    Processing data_subject resources...
    CREATED 15 data_subject resources.
    UPDATED 0 data_subject resources.
    SKIPPED 0 data_subject resources.
    ----------
    Processing data_category resources...
    CREATED 77 data_category resources.
    UPDATED 0 data_category resources.
    SKIPPED 0 data_category resources.
    ----------
    ```

1. `fidesctl ping` -> This confirms that your `fidesctl` CLI can reach the server and everything is ready to go!

    ```bash
    root@796cfde906f1:/fides/fidesctl# fidesctl ping
    Pinging http://fidesctl:8080/health...
    {
        "data": {
            "message": "Fidesctl API service is healthy!"
        }
    }
    ```

## Next Steps

Now that you're up and running, you can use `fidesctl` from the shell to get a list of all the possible CLI commands. You're now ready to start enforcing privacy with Fidesctl!

See the [Tutorial](../tutorial/overview.md) page for a step-by-step guide on setting up a Fidesctl data privacy workflow.
