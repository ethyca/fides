# Getting Started with Fidesctl in Docker

---

The recommended way to get Fidesctl running is via Docker. The following guide will describe how to get things going, step-by-step.

## System Requirements

Docker is the only requirement here. Install `docker` locally (see [Docker Desktop](https://www.docker.com/products/docker-desktop) or your preferred installation). The minimum verified Docker version is `20.10.8`

## Docker Setup

1. Create a network for your containers to use:

    ```shell
    docker network create fidesctl-net
    ```

1. Spin up a Postgres database:

    ```shell
    docker run --name postgres-docker --net fidesctl-net -d -e "POSTGRES_PASSWORD=postgres" -p 5432:5432 postgres:12
    ```

1. Start the Fidesctl webserver:

    ```shell
    docker run --name fidesctl-docker --net fidesctl-net -e "FIDESCTL__API__DATABASE_URL=postgresql+psycopg2://postgres:postgres@postgres-docker:5432/postgres" -p 8080:8080 -d ethyca/fidesctl fidesctl webserver
    ```

1. Attach a shell to the Fidesctl container:

    ```shell
    docker exec -it fidesctl-docker /bin/bash
    ```

1. Init the database:

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
